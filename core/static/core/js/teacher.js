$(document).ready(function() {
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

    // 定时刷新学生机状态（每5秒）
    function updateMachineStatus() {
        $.get('/machine-status/', function(data) {
            $('.machine-grid').empty();
            
            if (Object.keys(data).length === 0) {
                $('.machine-grid').html('<div class="text-center">当前没有学生在线</div>');
                return;
            }
            
            // 遍历所有在线学生并更新显示
            Object.entries(data).forEach(([ip, info]) => {
                const machineItem = $('<div>')
                    .addClass('machine-item')
                    .addClass('online');
                
                machineItem.append($('<div>')
                    .addClass('student-name')
                    .text(info.student_name));
                    
                machineItem.append($('<div>')
                    .addClass('login-time')
                    .text(`登录时间: ${info.last_login}`));
                
                $('.machine-grid').append(machineItem);
            });
        });
    }

    // 页面加载时立即更新一次
    updateMachineStatus();
    
    // 每5秒更新一次
    setInterval(updateMachineStatus, 5000);
}); 