from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, FileResponse, StreamingHttpResponse
from django.core.exceptions import PermissionDenied
import pandas as pd
from datetime import datetime
from .models import User, Assignment, DistributionLog
from .machine_monitor import MachineMonitor
from .assignment_handler import AssignmentDistributor
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from django.contrib import messages
import os
import urllib.parse
from django.core.files.base import ContentFile
from django.conf import settings
import shutil
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if not user.is_teacher:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
                
                user.ip_address = ip
                user.last_login = timezone.now()
                user.save(update_fields=['ip_address', 'last_login'])
                
                print(f"Student logged in - Sending WebSocket notification")
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "teacher_group",
                    {
                        "type": "student_status",
                        "data": {
                            "action": "login",
                            "student_id": user.student_id,
                            "name": user.first_name,
                            "ip": ip,
                            "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    }
                )
                print(f"WebSocket notification sent")
            
            return redirect('teacher_dashboard' if user.is_teacher else 'student_dashboard')
            
    return render(request, 'core/login.html')

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    # 获取所有作业任务
    assignments = Assignment.objects.all().select_related('assigned_to').order_by('-upload_time')
    
    # 获取所有班级列表（用于导出成绩的班级筛选）
    class_list = User.objects.filter(
        is_teacher=False
    ).values_list('class_name', flat=True).distinct().order_by('class_name')
    
    # 获取在线学生
    students = User.objects.filter(
        is_teacher=False,
        last_login__isnull=False,
        last_login__gte=timezone.now() - timezone.timedelta(minutes=5)
    )
    
    context = {
        'assignments': assignments,
        'class_list': class_list,  # 添加班级列表到上下文
        'students': students,
    }
    return render(request, 'core/teacher_dashboard.html', context)

@login_required
def student_dashboard(request):
    if request.user.is_teacher:
        raise PermissionDenied
        
    assignments = Assignment.objects.filter(assigned_to=request.user)
    context = {
        'assignments': assignments
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def import_students(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    if request.method == 'POST' and request.FILES.get('student_file'):
        try:
            df = pd.read_excel(request.FILES['student_file'])
            
            # 验证必需的列是否存在
            required_columns = ['学号', '姓名', '班级']
            if not all(col in df.columns for col in required_columns):
                messages.error(request, '文件格式错误，请使用正确的导入模板')
                return redirect('import_students')
            
            # 验证数据有效性
            success_count = 0
            error_messages = []
            
            for index, row in df.iterrows():
                try:
                    # 验证学号格式
                    if not str(row['学���']).isdigit():
                        error_messages.append(f"第{index+2}行：学号必须为数字")
                        continue
                        
                    # 验证姓名不为空
                    if pd.isna(row['姓名']) or str(row['姓名']).strip() == '':
                        error_messages.append(f"第{index+2}行：姓名不能为空")
                        continue
                    
                    # 检查学号是否已存在
                    if User.objects.filter(username=str(row['学号'])).exists():
                        error_messages.append(f"第{index+2}行：学号{row['学号']}已存在")
                        continue
                        
                    # 创建用户
                    User.objects.create_user(
                        username=str(row['学号']),
                        password=str(row['学号']),  # 初始密码设为学号
                        student_id=str(row['学号']),
                        first_name=str(row['姓名']),
                        class_name=str(row['班级']),
                        is_teacher=False
                    )
                    success_count += 1
                    
                except Exception as e:
                    error_messages.append(f"第{index+2}行：{str(e)}")
            
            # 显示导入结果
            if success_count > 0:
                messages.success(request, f'成功导入{success_count}条记录')
            if error_messages:
                messages.warning(request, '\n'.join(error_messages))
            
            if success_count > 0 and not error_messages:
                return redirect('teacher_dashboard')
            
        except Exception as e:
            messages.error(request, f'导入失败：{str(e)}')
    
    return render(request, 'core/import_students.html')

@login_required
def distribute_assignments(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    if request.method == 'POST' and request.FILES.getlist('assignments'):
        files = request.FILES.getlist('assignments')
        
        # 获取在线学生
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        online_students = list(User.objects.filter(
            is_teacher=False,
            last_login__gte=five_minutes_ago,
            ip_address__isnull=False
        ))
        
        if not online_students:
            return JsonResponse({'status': 'error', 'message': '当前没有在线学生'})
            
        try:
            assignments_created = 0
            student_index = 0  # 用于轮询分配
            total_students = len(online_students)
            
            # 直接遍历所有文件，轮询分配给在线学生
            for file in files:
                if total_students > 0:  # 确保有在线学生
                    # 获取当前学生
                    student = online_students[student_index]
                    
                    try:
                        # 生成唯一的文件名
                        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                        file_name = f"{timestamp}_{file.name}"
                        
                        # 创建作业记录
                        assignment = Assignment(
                            file_name=file.name,
                            assigned_to=student,
                            upload_time=timezone.now()
                        )
                        
                        # 使用 Django 的 FileField 保存文件
                        assignment.file_path.save(file_name, file, save=False)
                        assignment.save()
                        
                        print(f"Assignment created successfully:")
                        print(f"- ID: {assignment.id}")
                        print(f"- File name: {assignment.file_name}")
                        print(f"- File path: {assignment.file_path.path}")
                        print(f"- Assigned to: {student.username}")
                        
                        # 创建分发日志
                        DistributionLog.objects.create(
                            teacher=request.user,
                            student=student,
                            assignment=assignment,
                            status=True
                        )
                        
                        assignments_created += 1
                        
                        # 更新学生索引，实现轮询
                        student_index = (student_index + 1) % total_students
                        
                    except Exception as e:
                        print(f"Error creating assignment: {str(e)}")
                        continue
            
            if assignments_created > 0:
                return JsonResponse({
                    'status': 'success',
                    'message': f'成功分发{assignments_created}个作业任务给{total_students}个在线学生'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '没有成功分发任何作业'
                })
            
        except Exception as e:
            print(f"作业分发错误: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'作业分发失败: {str(e)}'
            })
    
    return render(request, 'core/distribute_assignments.html')

@login_required
def download_assignment(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id, assigned_to=request.user)
        
        print(f"开始处理下载请求:")
        print(f"- MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"- 文件相对路径: {assignment.file_path}")
        print(f"- 文件名: {assignment.file_name}")
        
        if not assignment.file_path:
            print("错误: 文件路径为空")
            return HttpResponse('文件不存在', status=404)
            
        try:
            file_path = os.path.join(settings.MEDIA_ROOT, str(assignment.file_path))
            print(f"- 完整文件路径: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"错误: 文件不存在于路径: {file_path}")
                return HttpResponse('文件不存在', status=404)
                
            # 使用 StreamingHttpResponse 替代 FileResponse
            def file_iterator(file_path, chunk_size=8192):
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk

            response = StreamingHttpResponse(
                file_iterator(file_path),
                content_type='application/octet-stream'
            )
            
            # 设置文件名，支持中文
            encoded_filename = urllib.parse.quote(assignment.file_name)
            response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
            
            # 更新下载状态
            assignment.download_status = True
            assignment.download_time = timezone.now()
            assignment.save(update_fields=['download_status', 'download_time'])
            
            print(f"文件下载成功: {assignment.file_name}")
            return response
                
        except Exception as e:
            print(f"文件读取错误: {str(e)}")
            return HttpResponse('文件读取失败', status=500)
            
    except Assignment.DoesNotExist:
        print(f"作业不存在: {assignment_id}")
        return HttpResponse('作业不存在', status=404)
    except Exception as e:
        print(f"下载过程中发生错误: {str(e)}")
        return HttpResponse('下载失败', status=500)

@login_required
def grade_assignment(request, assignment_id):
    if request.method == 'POST':
        grade = request.POST.get('grade')
        
        # 验证成绩格式
        if not grade or grade not in ['A', 'B', 'C', 'D']:
            return JsonResponse({
                'status': 'error',
                'message': '无效的成绩等级'
            })
            
        try:
            assignment = Assignment.objects.get(id=assignment_id, assigned_to=request.user)
            
            # 检查是否已经评分
            if assignment.grade:
                return JsonResponse({
                    'status': 'error',
                    'message': '该作业已经评过分'
                })
                
            # 更新成绩
            assignment.grade = grade
            assignment.save(update_fields=['grade'])
            
            return JsonResponse({
                'status': 'success',
                'grade_display': assignment.get_grade_display()
            })
            
        except Assignment.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '作业不存在'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'评分失败：{str(e)}'
            })
            
    return JsonResponse({
        'status': 'error',
        'message': '方法不允许'
    })

@login_required
def export_grades(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    try:
        # 获取选择的班级
        class_name = request.GET.get('class_name')
        
        # 构建查询条件
        query = {}
        if class_name:
            query['assigned_to__class_name'] = class_name
            
        # 获取作业数据
        assignments = Assignment.objects.filter(
            **query
        ).select_related('assigned_to').order_by(
            'assigned_to__class_name',
            'assigned_to__student_id',
            '-upload_time'
        )
        
        # 创建工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "成绩统计"
        
        # 设置表头
        headers = ['学号', '姓名', '班级', '作业名称', '成绩', '下载状态', '下载时间', '分配时间']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # 写入数据
        for row, assignment in enumerate(assignments, 2):
            student = assignment.assigned_to
            ws.cell(row=row, column=1).value = student.student_id
            ws.cell(row=row, column=2).value = student.first_name
            ws.cell(row=row, column=3).value = student.class_name
            ws.cell(row=row, column=4).value = assignment.file_name
            ws.cell(row=row, column=5).value = assignment.get_grade_display() if assignment.grade else '未评分'
            ws.cell(row=row, column=6).value = '已下载' if assignment.download_status else '未下载'
            ws.cell(row=row, column=7).value = timezone.localtime(assignment.download_time).strftime('%Y-%m-%d %H:%M:%S') if assignment.download_time else '-'
            ws.cell(row=row, column=8).value = timezone.localtime(assignment.upload_time).strftime('%Y-%m-%d %H:%M:%S')
        
        # 设置列宽
        column_widths = [15, 15, 15, 40, 10, 10, 20, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width
        
        # 创建响应
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # 设置文件名（包含班级信息和时间戳）
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"成绩统计_{class_name or '全部'}_{timestamp}.xlsx"
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{urllib.parse.quote(filename)}'
        
        # 保存到响应
        wb.save(response)
        return response
        
    except Exception as e:
        print(f"导出成绩时发生错误: {str(e)}")
        messages.error(request, f'导出失败：{str(e)}')
        return redirect('teacher_dashboard')

# 添加一个新的视图来更新机器状态
@login_required
def update_machine_status(request):
    # 如果是学生访问，返回空数据而不是抛出权限错误
    if not request.user.is_teacher:
        return JsonResponse({})
        
    # 获取最近5分钟内登录的所有学生
    five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
    students = User.objects.filter(
        is_teacher=False,
        last_login__gte=five_minutes_ago,
        ip_address__isnull=False
    ).order_by('ip_address')  # 按IP地址排序
    
    machine_status = {}
    for student in students:
        local_login_time = timezone.localtime(student.last_login)
        machine_status[student.ip_address] = {
            'online': True,
            'student_name': f"{student.first_name}({student.student_id})",
            'last_login': local_login_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return JsonResponse(machine_status)

@login_required
def logout_view(request):
    if not request.user.is_teacher:
        # 通知教师端
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "teacher_group",
            {
                "type": "student_status",
                "data": {
                    "action": "logout",
                    "student_id": request.user.student_id
                }
            }
        )
        
        request.user.ip_address = None
        request.user.save(update_fields=['ip_address'])
    
    logout(request)
    return redirect('login')

def download_import_template(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    # 创建新的Excel工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "学生信息导入模板"
    
    # 设置表头
    headers = ['学号', '姓名', '班级']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        # 设置表头样式
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    # 添加示例数据
    example_data = [
        ['2024001', '张三', '计算机1班'],
        ['2024002', '李四', '计算机1班']
    ]
    for row, data in enumerate(example_data, 2):
        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col).value = value
    
    # 设置宽度
    ws.column_dimensions['A'].width = 15  # 学号列
    ws.column_dimensions['B'].width = 15  # 姓名列
    ws.column_dimensions['C'].width = 20  # 班级列
    
    # 创建HTTP响应
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=student_import_template.xlsx'
    
    # 保存工作簿到响应
    wb.save(response)
    return response 

@login_required
def delete_assignment(request, assignment_id):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    if request.method == 'POST':
        try:
            assignment = Assignment.objects.get(id=assignment_id)
            
            # 如果文件存在，删除文件
            if assignment.file_path:
                try:
                    assignment.file_path.delete(save=False)
                except Exception as e:
                    print(f"删除文件错误: {str(e)}")
            
            # 删除作业记录
            assignment.delete()
            
            return JsonResponse({'status': 'success'})
            
        except Assignment.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '作业不存在'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': '方法不允许'
    })

@login_required
@require_http_methods(["POST"])
def delete_assignments(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    try:
        data = json.loads(request.body)
        assignment_ids = data.get('assignment_ids', [])
        
        if not assignment_ids:
            return JsonResponse({
                'status': 'error',
                'message': '未选择要删除的作业'
            })
            
        assignments = Assignment.objects.filter(id__in=assignment_ids)
        deleted_count = 0
        
        for assignment in assignments:
            try:
                # 删除文件
                if assignment.file_path:
                    assignment.file_path.delete(save=False)
                # 删除记录
                assignment.delete()
                deleted_count += 1
            except Exception as e:
                print(f"删除作业 {assignment.id} 时出错: {str(e)}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'成功删除 {deleted_count} 个作业任务'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': '��效的请求数据'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })