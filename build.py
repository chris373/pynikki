import os
import shutil
from distutils.dir_util import copy_tree # used for copying inner contets of directory
import math
from collections import namedtuple
from jinja2 import Environment, PackageLoader
import json
import time
import copy

class json_handler:
    def load(self, filename):
        with open(filename, 'r') as json_data:
            return json.load(json_data)
    def write(self, filename, json_data):
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=4)


class archive:
    def __init__(self, filename, json_handler):
        self.json_data = json_handler.load(filename)
    def update(self, element_dict):
        self.json_data.update(element_dict)


class jinja_templater:
    def __init__(self, config):
        self.env = Environment(loader=PackageLoader(config['site_path'], config['templates_path']))
    def apply(self, apply_template, output, **kwargs):
        template = self.env.get_template(apply_template)
        with open(output, 'w') as f:
            f.write(template.render(kwargs))


def paginate(config, posts, sort_key, per_page_count):
    # sort, then reverse for chronological order
    # change each post to a tuple of (post[sort_key], post)
    posts = [(posts[post][sort_key], posts[post]) for post in posts]
    posts = sorted(posts, key=lambda post: float(post[0]))[::-1]
    # change it back to just the post
    posts = [post[1] for post in posts]
    pages = [[] for i in range(0, math.ceil( len(posts) / float(per_page_count) ))]
    for i in range(0, len(posts)):
        pages[math.floor(i / int(per_page_count))].append(posts[i])
    return pages


def load_content(filename):
    with open(filename, 'r') as f:
        content = f.read()
    return content


def build_site(config, archive, templater):
    # build archive page(s)
    archive_pages = paginate(config, archive, 'mtime', config['archive_pagination_count'])
    for i, page in enumerate(archive_pages):
        buttons = get_buttons(i, len([k for k in archive]), config['archive_pagination_count'], config['pagination_button_count'])
        save_to = os.path.join(config['site_path'], 'archive', str(i) + '.html')
        templater.apply(config['archive_template'], save_to, posts=page, buttons=buttons)

    # build blog page(s)
    blog_pages = paginate(config, archive, 'mtime', config['blog_pagination_count'])
    # each post in blog_pages does not contain the posts content, load it in.
    for page in blog_pages:
        for post in page:
            post['content'] = load_content(os.path.join(config['posts_path'], post['filename']))
    for i, page in enumerate(blog_pages):
        buttons = get_buttons(i, len([k for k in archive]), config['blog_pagination_count'], config['pagination_button_count'])
        save_to = os.path.join(config['site_path'], 'blog', str(i) + '.html')
        templater.apply(config['blog_template'], save_to, posts=page, buttons=buttons)


def update_archive(config, archive):
    # if it's not in the archive, add it
    # os.walk yields a 3-tuple (dirpath, dirnames, filenames)
    step = next(os.walk(config['posts_path']))
    files_directory = step[0]
    files = step[2]
    for f in files:
        if f not in archive:
            archive[f] = {}
            fdict = archive[f]
            t = os.path.getmtime(files_directory + '/' + f)
            fdict['mtime'] = str(t)
            gmt = time.gmtime(t)
            fdict['publish_date'] = time.strftime(config['date_format_string'], gmt)
            fdict['title'] = '.'.join(f.split('.')[:-1])
            fdict['filename'] = f


def get_buttons(cur_page, post_count, pagination_count, button_count):
    post_count = int(post_count)
    pagination_count = int(pagination_count)
    button_count = int(button_count)

    page_count = int(math.ceil(post_count / float(pagination_count)))
    halfb = int(button_count/2)
    lhalf = page_count - halfb
    if cur_page < halfb:
        newb = [b for b in range(0, button_count)]
    elif cur_page >= lhalf:
        newb = [b for b in range(page_count - button_count, page_count)]
    else:
        newb = [b for b in range(cur_page - int(button_count/2), cur_page + int(button_count/2) +1)]
    newb = [nb if nb >= 0 and nb < page_count else '' for nb in newb]

    button_dicts = []
    for nb in newb:
        if nb == '' or cur_page == nb:
            button_dicts.append({'active': 'disabled', 'number': str(nb),
                                'link': '#'})
        else:
            button_dicts.append({'active': 'active', 'number': str(nb),
                                    'link': str(nb) + '.html'})

    # add first, back, forward, last
    first_back_active = cur_page != 0
    last_forward_active = cur_page != page_count - 1
    if first_back_active :
        first_back_active = 'active'
        first_link = str(0) + '.html'
        back_link =  str(cur_page - 1) + '.html'
    else:
        first_back_active = 'disabled'
        first_link = '#'
        back_link = '#'

    if last_forward_active:
        last_forward_active = 'active'
        last_link = str(page_count - 1) + '.html'
        forward_link = str(cur_page + 1) + '.html'
    else:
        last_forward_active = 'disabled'
        last_link = '#'
        forward_link = '#'

    button_dicts.insert(0, {'active': first_back_active, 'link': back_link })
    button_dicts.insert(0, {'active': first_back_active, 'link': first_link })
    button_dicts.append({'active': last_forward_active, 'link': forward_link })
    button_dicts.append({'active': last_forward_active, 'link': last_link })
    return button_dicts


def file_setup(config):
    # remove the old verison of the site and recreate the folder
    shutil.rmtree(config['site_path'], ignore_errors=True)
    os.makedirs(config['site_path'], exist_ok=False)
    # move static files over
    copy_tree('static', config['site_path'])
    shutil.copytree('css', config['site_path'] + '/css')
    shutil.copytree(config['templates_path'], config['site_path'] + '/templates')
  # use indent of 4 for readability
    # create a folder to hold blog posts
    os.makedirs(config['site_path'] + '/blog')
    # create a folder to hold blog posts
    os.makedirs(config['site_path'] + '/archive')
    with open(os.path.join(config['site_path'], '__init__.py'), 'w') as f:
        f.write('')


def build():
    jsonhandler = json_handler()
    config = jsonhandler.load('config.json')
    archive = jsonhandler.load('archive.json')
    file_setup(config)
    templater = jinja_templater(config)
    update_archive(config, archive)
    jsonhandler.write('archive.json', archive)
    build_site(config, archive, templater)

build()
