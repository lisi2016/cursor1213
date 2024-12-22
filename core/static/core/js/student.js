$(document).ready(function() {
    // 定义刷新间隔（毫秒）
    const REFRESH_INTERVAL = 30000; // 30秒

    // 刷新作业列表函数
    function refreshAssignmentList() {
        $.ajax({
            url: '/student/assignments/',  // 新添加的API端点
            type: 'GET',
            success: function(response) {
                // 更新作业列表
                const assignmentTable = $('.table tbody');
                if (response.assignments.length === 0) {
                    assignmentTable.html('<tr><td colspan="5" class="text-center">暂无作业</td></tr>');
                } else {
                    let html = '';
                    response.assignments.forEach(assignment => {
                        html += `
                            <tr>
                                <td>${assignment.file_name}</td>
                                <td>${assignment.upload_time}</td>
                                <td>${assignment.download_status ? '已下载' : '未下载'}</td>
                                <td>${assignment.grade || '-'}</td>
                                <td>
                                    <div class="btn-group">
                                        <a href="/download-assignment/${assignment.id}/" 
                                           class="btn btn-sm btn-primary download-btn"
                                           data-assignment-id="${assignment.id}">下载</a>
                                        ${!assignment.grade ? `
                                            <button type="button" 
                                                    class="btn btn-sm btn-success grade-btn"
                                                    data-assignment-id="${assignment.id}">
                                                评分
                                            </button>
                                        ` : ''}
                                    </div>
                                </td>
                            </tr>
                        `;
                    });
                    assignmentTable.html(html);
                }
            },
            error: function(xhr) {
                console.error('刷新作业列表失败:', xhr);
            }
        });
    }

    // 设置定时刷新
    setInterval(refreshAssignmentList, REFRESH_INTERVAL);

    // 页面加载完成后立即刷新一次
    refreshAssignmentList();

    // 作业评分
    $('.grade-btn').on('click', function() {
        var assignmentId = $(this).data('assignment-id');
        var grade = prompt('请选择评分等级 (A/B/C/D)：');
        
        if (grade && /^[A-D]$/i.test(grade)) {
            // 显示加载状态
            var $btn = $(this);
            $btn.prop('disabled', true).text('评分中...');
            
            $.ajax({
                url: '/grade-assignment/' + assignmentId + '/',
                type: 'POST',
                data: {
                    grade: grade.toUpperCase(),
                    csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.status === 'success') {
                        // 更新UI显示
                        var $row = $btn.closest('tr');
                        $row.find('td:eq(3)').text(getGradeDisplay(grade)); // 更新成绩列
                        $btn.remove(); // 移除评分按钮
                        
                        // 显示成功提示
                        alert('评分成功！');
                    } else {
                        alert('评分失败：' + response.message);
                        // 恢复按钮状态
                        $btn.prop('disabled', false).text('评分');
                    }
                },
                error: function() {
                    alert('系统错误，请稍后重试');
                    // 恢复按钮状态
                    $btn.prop('disabled', false).text('评分');
                }
            });
        } else if (grade !== null) { // 用户输入了无效的成绩
            alert('请输入有效的评分等级（A/B/C/D）');
        }
    });
    
    // 辅助函数：获取成绩显示文本
    function getGradeDisplay(grade) {
        const gradeMap = {
            'A': '优',
            'B': '良',
            'C': '合格',
            'D': '差'
        };
        return gradeMap[grade.toUpperCase()] || grade;
    }
}); 