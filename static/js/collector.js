function add_impression(user_id, event_type, content_id, session_id, csrf_token) {
            $.ajax({
                 type: 'POST',
                 url: '/collect/log/',
                 data: {
                        "csrfmiddlewaretoken": csrf_token,
                        "event_type": event_type,
                        "user_id": user_id,
                        "content_id": content_id,
                        "session_id": session_id
                        },
                 fail: function(){
                     console.log('log failed(' + event_type + ')')
                    }
            })};