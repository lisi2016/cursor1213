$(document).ready(function() {
    // 作业评分
    $('.grade-btn').on('click', function() {
        var assignmentId = $(this).data('assignment-id');
        var grade = prompt('请选择评分等级 (A/B/C/D)：');
        
        if (grade && /^[A-D]$/i.test(grade)) {
            $.ajax({
                url: '/grade-assignment/' + assignmentId + '/',
                type: 'POST',
                data: {
                    grade: grade.toUpperCase(),
                    csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.status === 'success') {
                        location.reload();
                    } else {
                        alert('评分失败：' + response.message);
                    }
                },
                error: function() {
                    alert('系统错误，请稍后重试');
                }
            });
        }
    });
}); 