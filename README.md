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

