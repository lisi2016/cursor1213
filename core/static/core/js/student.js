$(document).ready(function() {
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