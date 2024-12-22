$(document).ready(function() {
    const wsStatus = $('#ws-status');
    const wsStatusText = $('#ws-status-text');
    
    let socket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    function connectWebSocket() {
        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const ws_path = ws_scheme + '://' + window.location.host + '/ws/student_status/';
        console.log('=== WebSocket Connection Debug ===');
        console.log('Attempting to connect to:', ws_path);
        console.log('Current protocol:', window.location.protocol);
        console.log('Current host:', window.location.host);
        
        try {
            socket = new WebSocket(ws_path);

            socket.onopen = function(e) {
                console.log('WebSocket connection established:', e);
                wsStatusText.text('已连接');
                wsStatus.removeClass('alert-info alert-danger').addClass('alert-success');
                reconnectAttempts = 0;
            };

            socket.onmessage = function(e) {
                console.log('WebSocket message received:', e.data);
                try {
                    const data = JSON.parse(e.data);
                    console.log('Parsed message data:', data);
                    
                    if (data.action === 'login') {
                        console.log('Processing student login:', data);
                        updateStudentStatus(data);
                    } else if (data.action === 'logout') {
                        console.log('Processing student logout:', data);
                        removeStudentStatus(data.student_id);
                    }
                } catch (error) {
                    console.error('Error processing WebSocket message:', error);
                }
            };

            socket.onclose = function(e) {
                console.error('WebSocket connection closed:', {
                    code: e.code,
                    reason: e.reason,
                    wasClean: e.wasClean
                });
                wsStatusText.text('连接已断开');
                wsStatus.removeClass('alert-info alert-success').addClass('alert-danger');
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
                    wsStatusText.text(`正在重连 (${reconnectAttempts}/${maxReconnectAttempts})...`);
                    setTimeout(connectWebSocket, 3000);
                } else {
                    console.log('Max reconnection attempts reached');
                    wsStatusText.text('连接失败，请刷新页面重试');
                }
            };

            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
                wsStatusText.text('连接错误');
                wsStatus.removeClass('alert-info alert-success').addClass('alert-danger');
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            wsStatusText.text('连接失败');
            wsStatus.removeClass('alert-info alert-success').addClass('alert-danger');
        }
    }

    // 初始连接
    connectWebSocket();

    // 添加这两个关键函数
    function updateStudentStatus(data) {
        const studentBox = `
            <div class="machine-item online" data-student-id="${data.student_id}">
                <div class="student-name">${data.name}</div>
                <div class="ip-address">IP: ${data.ip}</div>
                <div class="login-time">登录时间: ${data.last_login}</div>
            </div>
        `;
        
        $(`.machine-item[data-student-id="${data.student_id}"]`).remove();
        $('.machine-grid').append(studentBox);
        
        if ($('.machine-grid .machine-item').length === 1) {
            $('.machine-grid .text-center').remove();
        }
    }

    function removeStudentStatus(studentId) {
        $(`.machine-item[data-student-id="${studentId}"]`).remove();
        
        if ($('.machine-grid .machine-item').length === 0) {
            $('.machine-grid').html('<div class="text-center">当前没有学生在线</div>');
        }
    }

    // 页面关闭前关闭 WebSocket
    window.onbeforeunload = function() {
        if (socket) {
            socket.close();
        }
    };

    // 在发送请求前获取CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 修改分发作业的AJAX请求
    $('#assignmentForm').on('submit', function(e) {
        e.preventDefault();
        
        // 添加详细日志
        console.log('=== Form Submit Triggered ===');
        console.log('Form action:', $(this).attr('action'));
        console.log('CSRF token:', $('[name=csrfmiddlewaretoken]').val());
        
        // 检查FormData内容
        const formData = new FormData(this);
        console.log('FormData entries before processing:');
        for (let pair of formData.entries()) {
            console.log(pair[0], pair[1]);
        }
        
        // 检查文件
        const files = $('#assignments')[0].files;
        console.log('Files selected:', {
            count: files.length,
            details: Array.from(files).map(f => ({
                name: f.name,
                size: f.size,
                type: f.type
            }))
        });

        // 检查在线学生
        const onlineStudents = [];
        $('.machine-item.online').each(function() {
            const studentId = $(this).data('student-id');
            console.log('Processing student element:', this);
            console.log('Found student ID:', studentId);
            if (studentId) {
                onlineStudents.push(studentId);
            }
        });
        console.log('Final online students list:', onlineStudents);

        // 在发送请求前再次检查
        console.log('=== Pre-request Check ===');
        console.log('URL:', $(this).attr('action'));
        console.log('Method: POST');
        console.log('CSRF token present:', !!$('[name=csrfmiddlewaretoken]').val());
        console.log('Files count:', files.length);
        console.log('Students count:', onlineStudents.length);

        // 1. 检查文件
        if (files.length === 0) {
            alert('请选择要分发的文件');
            return;
        }

        // 2. 检查在线学生
        if (onlineStudents.length === 0) {
            alert('当���没有在线学生');
            return;
        }

        // 3. 准备表单数据
        const formData = new FormData(this);
        formData.set('student_ids', JSON.stringify(onlineStudents));
        
        console.log('表单数据:', {
            url: $(this).attr('action'),
            method: 'POST',
            studentIds: JSON.stringify(onlineStudents),
            csrf: $('[name=csrfmiddlewaretoken]').val()
        });

        // 显示加载状态
        const submitBtn = $(this).find('button[type="submit"]');
        const originalText = submitBtn.find('.button-text').text();
        submitBtn.prop('disabled', true);
        submitBtn.find('.button-text').text('分发中...');

        // 发送请求
        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                console.log('发送请求前:', {
                    url: this.url,
                    method: this.type,
                    headers: xhr.getAllResponseHeaders()
                });
            },
            success: function(response) {
                console.log('请求成功:', response);
                if (response.status === 'success') {
                    alert(response.message);
                    location.reload();
                } else {
                    alert(response.message || '分发失败，请重试');
                }
            },
            error: function(xhr, status, error) {
                console.error('请求失败:', {
                    status: xhr.status,
                    statusText: xhr.statusText,
                    responseText: xhr.responseText,
                    error: error
                });
                try {
                    const response = JSON.parse(xhr.responseText);
                    alert(response.message || '系统错误，请稍后重试');
                } catch (e) {
                    console.error('解析错误响应失败:', e);
                    alert('系统错误，请稍后重试');
                }
            },
            complete: function() {
                console.log('请求完成');
                submitBtn.prop('disabled', false);
                submitBtn.find('.button-text').text(originalText);
            }
        });
    });

    // 处理全选/取消全选
    $('#selectAll').on('change', function() {
        const isChecked = $(this).prop('checked');
        $('.assignment-checkbox').prop('checked', isChecked);
        updateBatchDeleteButton();
    });

    // 处理单个复���框变化
    $('.assignment-checkbox').on('change', function() {
        updateBatchDeleteButton();
        // 如果取消选中某个复选框，也要更新全选框状态
        const allChecked = $('.assignment-checkbox:checked').length === $('.assignment-checkbox').length;
        $('#selectAll').prop('checked', allChecked);
    });

    // 处理批量删除按钮点击
    $('#batchDeleteBtn').on('click', function() {
        const selectedIds = $('.assignment-checkbox:checked').map(function() {
            return $(this).data('assignment-id');
        }).get();

        if (selectedIds.length > 0) {
            if (confirm(`确定要删除选中的 ${selectedIds.length} 个批改任务吗？此操作不可恢复。`)) {
                deleteAssignments(selectedIds);
            }
        }
    });

    // 更新批量删除按钮显示状态
    function updateBatchDeleteButton() {
        const selectedCount = $('.assignment-checkbox:checked').length;
        $('#batchDeleteBtn').toggle(selectedCount > 0);
    }

    // 删除作业的通用函数
    function deleteAssignments(assignmentIds) {
        if (!Array.isArray(assignmentIds) || assignmentIds.length === 0) return;

        $.ajax({
            url: '/delete-assignments/',
            type: 'POST',
            data: JSON.stringify({ assignment_ids: assignmentIds }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.status === 'success') {
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

    function distributeAssignments(files, selectedStudents) {
        // 创建 FormData 对象
        const formData = new FormData();
        
        // 添加文件
        for (let file of files) {
            formData.append('assignments', file);
        }
        
        // 添加学生ID列表
        formData.append('student_ids', JSON.stringify(selectedStudents));
        
        // 发送请求
        $.ajax({
            url: '/distribute-assignments/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')  // 添加 CSRF token
            },
            success: function(response) {
                if (response.status === 'success') {
                    alert(response.message);
                    location.reload();
                } else {
                    alert('分发失败：' + response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Distribution error:', {xhr, status, error});
                try {
                    const response = JSON.parse(xhr.responseText);
                    alert('分发失败：' + response.message);
                } catch (e) {
                    console.error('Error parsing error response:', e);
                    alert('分发失败：系统错误');
                }
            }
        });
    }
}); 