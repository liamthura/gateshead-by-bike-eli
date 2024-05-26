from pywebio import *
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_js

smaller_font_clicks = 0
bigger_font_clicks = 0
dark_mode = False
dark_mode_css = """
            <div style="display: none">
                <style>
                    body, .footer {background-color: #333; color: white;}
                    footer {margin-top: auto;}
                    div {background-color: #444; color: white}
                    #input-cards, #input-container  {background-color: #444; white}
                    .card-header, .card-footer {background-color: #4a4a4a;}
                </style>
            </div>
"""


@use_scope('ROOT')
def main():
    clear()
    generate_header()
    user_data = {'username': 'khantthura',
                 'date': '12-05-2024',
                 'display_name': 'Khant Thura',
                 'content': 'This is a test content to see if the function is working'}

    generate_card(user_data)

    # put_buttons(['Login', 'Register'], onclick=[login, register])


def edit_content():
    clear()
    generate_header()
    user_data = input_group('Edit Content', [
        textarea('Content', name='content', value='This is a test content to see if the function is working')
    ], cancelable=True)

    if user_data is None:
        run_js('window.location.href = "/"')


# function that switches between dark and light mode
def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    print(dark_mode)
    run_js('window.location.reload()')


def smaller_font():
    global smaller_font_clicks, bigger_font_clicks
    js_code = f'''
        let allElements = document.querySelectorAll('p,h2,h3,h4,h5,h6');
        allElements.forEach(function(element) {{
            var style = window.getComputedStyle(element, null).getPropertyValue('font-size');
            var currentSize = parseFloat(style);
            if ({smaller_font_clicks} < 5) {{
                element.style.fontSize = (currentSize - 1) + "px";
            }} else {{
                return;
            }}
        }});
    '''
    if smaller_font_clicks < 5:
        smaller_font_clicks += 1
        bigger_font_clicks -= 1
    run_js(js_code)
    print(smaller_font_clicks, bigger_font_clicks)


def bigger_font():
    global smaller_font_clicks, bigger_font_clicks
    js_code = f'''
            let allElements = document.querySelectorAll('p, h2, h3, h4, h5, h6');
            allElements.forEach(function(element) {{
                var style = window.getComputedStyle(element, null).getPropertyValue('font-size');
                var currentSize = parseFloat(style);
                if ({bigger_font_clicks} < 6) {{
                    element.style.fontSize = (currentSize + 1) + "px";
                }} else {{
                    return;
                }}
            }});
        '''
    if bigger_font_clicks < 6:
        bigger_font_clicks += 1
        smaller_font_clicks -= 1
    run_js(js_code)
    print(smaller_font_clicks, bigger_font_clicks)


def generate_header():
    if dark_mode:
        put_html(dark_mode_css)
    global smaller_font_clicks, bigger_font_clicks
    smaller_font_clicks, bigger_font_clicks = 0, 0
    put_buttons([
        {'label': '+', 'value': 'bigger', 'color': 'primary'},
        {'label': '-', 'value': 'smaller', 'color': 'info'},
        {'label': 'Dark Mode', 'value': 'dark_mode', 'color': 'dark'}
    ], onclick=[bigger_font, smaller_font, toggle_dark_mode]).style(
        'float:right')
    put_html(f'''
        <h1>
        Welcome to GBB-ELI
        <p class="h5">A parking lot management system for Gateshead Bike Users</p>
        </h1>
        ''')


# function to generate a card from post data
def generate_card(post):
    put_html(f'''
        <div class="card">
            <div class="card-header">
            <h3 class="card-title" style="margin: 8px 0;">
                {post['display_name']}
                <small class="text-body-secondary">{post['date']}</small>
            </h3>
            </div>
            <div class="card-body">
                <p>{post['content']}.</p>
            </div>
            <div class="card-footer">
                <a href="/?app=edit"><button class="btn btn-primary">Edit</button></a>
                <button class="btn btn-danger">Delete</button>
            </div>
        </div>
        ''')


if __name__ == '__main__':
    routes = {
        'index': main,
        'edit': edit_content,
        'bigger': bigger_font
    }
    start_server(routes, port=8080, host='localhost', debug=True)

    # notification_table_data = []
    # serialNum = 1
    # for notification in notifications:
    #     notificationDateTime = notification.date_time.strftime('%I:%M%p – %d %b, %Y')
    #     notification_table_data.append([
    #         serialNum,
    #         notification.title,
    #         notification.content,
    #         notificationDateTime
    #     ])
    #     serialNum += 1
    # put_table(notification_table_data, header=[
    #     'No',
    #     'Title',
    #     'Content',
    #     'Date'
    # ])
