$(document).ready(function() {
    // WebSocket 连接
    const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const ws_path = ws_scheme + '://' + window.location.host + '/ws/student_status/';
    const socket = new WebSocket(ws_path);

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        if (data.action === 'login') {
            // 添加或更新学生状态
            updateStudentStatus(data);
        } else if (data.action === 'logout') {
            // 移除学生状态
            removeStudentStatus(data.student_id);
        }
    };

    socket.onclose = function(e) {
        console.error('WebSocket closed unexpectedly');
    };

    function updateStudentStatus(data) {
        const studentBox = `
            <div class="machine-item online" data-student-id="${data.student_id}">
                <div class="student-name">${data.name}</div>
                <div class="ip-address">IP: ${data.ip}</div>
                <div class="login-time">登录时间: ${data.last_login}</div>
            </div>
        `;
        
        // 移除��的状态（如果存在）
        $(`.machine-item[data-student-id="${data.student_id}"]`).remove();
        
        // 添加新状态
        $('.machine-grid').append(studentBox);
        
        // 如果是第一个学生，移除"无学生在线"提示
        if ($('.machine-grid .machine-item').length === 1) {
            $('.machine-grid .text-center').remove();
        }
    }

    function removeStudentStatus(studentId) {
        $(`.machine-item[data-student-id="${studentId}"]`).remove();
        
        // 如果没有学生在线，显示提示
        if ($('.machine-grid .machine-item').length === 0) {
            $('.machine-grid').html('<div class="text-center">当前没有学生在线</div>');
        }
    }

    // 作业分发表单提交
    $('#assignmentForm').on('submit', function(e) {
        e.preventDefault();
        
        var formData = new FormData(this);
        
        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.status === 'success') {
                    alert('作业分发成功！');
                    location.reload();
                } else {
                    alert('作业分发失败：' + response.message);
                }
            },
            error: function() {
                alert('系统错误，请稍后重试');
            }
        });
    });

    // 处理删除批改任务
    $('.delete-assignment').on('click', function() {
        const assignmentId = $(this).data('assignment-id');
        
        if (confirm('确定要删除这个批改任务吗？此操作不可恢复。')) {
            $.ajax({
                url: `/delete-assignment/${assignmentId}/`,
                type: 'POST',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.status === 'success') {
                        // 删除成功后刷新页面
                        location.reload();
                    } else {
                        alert('删除失败：' + response.message);
                    }
                },
                error: function() {
                    alert('系统错误，请稍后重试');
                }
            });
        }
    });

    // 初始化工具提示
    $('[data-bs-toggle="tooltip"]').tooltip();

    // 处理导出成绩表单提交
    $('#exportForm').on('submit', function(e) {
        // 显示加载提示
        const submitBtn = $(this).find('button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>导出中...');
        
        // 导出完成后恢复按钮状态
        setTimeout(() => {
            submitBtn.prop('disabled', false).html(originalText);
        }, 3000);
    });
}); 