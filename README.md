# shaberou
Shaberou is a static page generator focused on helping you easily create a blog using jinja2 templates.

to get started first install Jinja 2.
using pip: ```pip install Jinja2```

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

the default configuration looks for posts inside publish, and templates inside myblog/templates
The configurations settings are in the config array inside the archive.json file.

This project comes with some dummy posts and a simple Jinja2 template. To try them out just run it with:
```python build.py```

This will place the generated pages inside myblog/blog/<n>.html

The pagination and page buttons are handled for you and are automatically created for you. 
The default is to create a first and last page button, and back and forward buttons.
These get passed into the jinja2 template as list of buttons. 
the buttons have their page number, active, and the appropriate link. 

Look under ```<!-- paginate -->``` to see how the buttons are accessed.

