# Pynikki

pynikki is a static page generator focused on helping you easily create a blog using jinja2 templates for the layout and markdown to create your posts.
I use pynikki to publish my blog at [chris373.github.io](https://chris373.github.io)

pynikki will handle pagination automatically, with no extra plugins to configure.

Installation
---------------
to get started first install Jinja 2.
using pip: ```pip install Jinja2```
This project comes with some dummy posts and a simple Jinja2 template. To try them out just run it with:
```python build.py```
That's all there is to it! Now the blog pages are available under myblog/blog

Overview
--------------
The default structure looks like this:
```
.
├── archive.json
├── build.py
├── myblog
│   ├── blog
│   ├── css
│   │   └── blog.css
│   ├── __init__.py
│   └── templates
│       └── blog_template.html
└── publish
    ├── post001.txt
    ├── post002.txt
    ├── post003.txt
    ├── post004.txt
    ├── post005.txt
    ├── post006.txt
    └── post007.txt
    └── ...
```

The configurations settings are inside the config.json file.
the default configuration looks for posts inside publish, and for the template myblog/blog_template.html
building the site will place the generated pages inside myblog/blog/<n>.html

The pagination and page buttons are automatically handled for you based on settings inside config. 
The default creates a list of buttons in the order ```[first_page, back, n1, n2, n3, n4, n5, forward, last_page]```
 
each button is a dictionary containing page number, whether or not it is active active, and the appropriate page link. 
Look under ```<!-- paginate -->``` in myblog/blog_template.html to see how to access the buttons for your Jinja2 template.
