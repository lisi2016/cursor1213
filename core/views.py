from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, FileResponse
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

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if not user.is_teacher:
                # 获取客户端真实IP地址
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0].strip()
                else:
                    ip = request.META.get('REMOTE_ADDR')
                
                # 更新用户IP和登录时间
                user.ip_address = ip
                user.last_login = timezone.now()
                user.save(update_fields=['ip_address', 'last_login'])
                print(f"Student logged in - Username: {username}, IP: {ip}")  # 添加调试日志
            
            return redirect('teacher_dashboard' if user.is_teacher else 'student_dashboard')
            
    return render(request, 'core/login.html')

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    # 只获取已登录的学生
    students = User.objects.filter(
        is_teacher=False,
        last_login__isnull=False,
        # 只获取最近5分钟内登录的学生
        last_login__gte=timezone.now() - timezone.timedelta(minutes=5)
    )
    
    machine_status = {}
    for student in students:
        if student.ip_address:  # 只有登录的学生才会有IP地址
            machine_status[student.ip_address] = {
                'online': True,
                'student_name': student.first_name,
                'last_login': student.last_login
            }
            
    context = {
        'machine_status': machine_status,
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
                    if not str(row['学号']).isdigit():
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
            # 按IP地址前缀对文件进行分组
            file_groups = {}
            for file in files:
                # 假设文件名格式为: "192.168.1.100_作业1.doc"
                ip_prefix = file.name.split('_')[0]  # 获取IP地址前缀
                if ip_prefix not in file_groups:
                    file_groups[ip_prefix] = []
                file_groups[ip_prefix].append(file)
            
            assignments_created = 0
            
            # 为每组作业分配学生
            for ip_prefix, group_files in file_groups.items():
                # 如果学生数量少于作业数，每个学生至少分配一份作业
                students_for_group = online_students[:len(group_files)]
                if not students_for_group:
                    continue
                    
                # 分配作业给学生
                for file in group_files:
                    # 如果还有未分配的学生，就分配给下一个学生
                    if students_for_group:
                        student = students_for_group.pop(0)
                        
                        # 创建作业记录
                        assignment = Assignment(
                            file_name=file.name,
                            assigned_to=student,
                            upload_time=timezone.now()
                        )
                        assignment.save()
                        
                        # 保存文件
                        assignment.file_path.save(file.name, file, save=True)
                        
                        # 创建分发日志
                        DistributionLog.objects.create(
                            teacher=request.user,
                            student=student,
                            assignment=assignment,
                            status=True
                        )
                        
                        assignments_created += 1
            
            return JsonResponse({
                'status': 'success',
                'message': f'成功分发{assignments_created}个作业任务'
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
        
        if not assignment.file_path:
            return HttpResponse('文件不存在', status=404)
            
        try:
            file_path = assignment.file_path.path
            if not os.path.exists(file_path):
                return HttpResponse('文件不存在', status=404)
                
            # 使用 FileResponse 替代 HttpResponse
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{urllib.parse.quote(assignment.file_name)}"'
            
            # 更新下载状态
            assignment.download_status = True
            assignment.download_time = timezone.now()
            assignment.save()
            
            return response
            
        except Exception as e:
            print(f"文件下载错误: {str(e)}")
            return HttpResponse('文件下载失败', status=500)
            
    except Assignment.DoesNotExist:
        raise PermissionDenied

@login_required
def grade_assignment(request, assignment_id):
    if request.method == 'POST':
        grade = request.POST.get('grade')
        try:
            assignment = Assignment.objects.get(id=assignment_id, assigned_to=request.user)
            assignment.grade = grade
            assignment.save()
            return JsonResponse({'status': 'success'})
        except Assignment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '作业不存在'})
            
    return JsonResponse({'status': 'error', 'message': '方法不允许'})

@login_required
def export_grades(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
    class_name = request.GET.get('class_name')
    assignments = Assignment.objects.filter(
        assigned_to__class_name=class_name if class_name else None
    ).select_related('assigned_to')
    
    data = []
    for assignment in assignments:
        data.append({
            '学号': assignment.assigned_to.student_id,
            '姓名': assignment.assigned_to.first_name,
            '班级': assignment.assigned_to.class_name,
            '作业': assignment.file_name,
            '成绩': assignment.grade,
            '下载时间': assignment.download_time
        })
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="grades.xlsx"'
    df.to_excel(response, index=False)
    return response 

# 添加一个新的视图来更新机器状态
@login_required
def update_machine_status(request):
    if not request.user.is_teacher:
        raise PermissionDenied
        
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

def logout_view(request):
    if request.user.is_authenticated and not request.user.is_teacher:
        # 清除学生的IP地址
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
    ws.column_dimensions['B'].width = 15  # ��名列
    ws.column_dimensions['C'].width = 20  # 班级列
    
    # 创建HTTP响应
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=student_import_template.xlsx'
    
    # 保存工作簿到响应
    wb.save(response)
    return response 