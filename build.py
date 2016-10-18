import os
import shutil
from distutils.dir_util import copy_tree # used for copying inner contets of directory
import math
from collections import namedtuple
from jinja2 import Environment, PackageLoader
import json
import time
import copy
import markdown

def cast(value, cast_type):
    if cast_type == 'int':
        return int(value)
    if cast_type == 'float':
        return float(value)
    if cast_type == 'string':
        return str(value)


def get_extension(file):
    return file.split('.')[-1]

def remove_extensions(file):
    return '.'.join(file.split('.')[:-1])


def write_changes(json_data):
    json_data_str = json.dumps(json_data)
    json_config_str = json.dumps(json_data['config'])
    with open('config.json', 'w') as f:
        json.dump(json_data['config'], f, indent=4)
    json_data.pop('config')
    with open('archive.json', 'w') as f:
        json.dump(json_data, f, indent=4)

def get_config(json_data):
    config = json_data['config']
    cdict = dict()
    for con in config:
        contype = con['type']
        keys = [key for key in con]
        # remove type, leaving only the config value
        keys.remove('type')
        cdict[keys[0]] = cast(con[keys[0]], contype)
    return cdict


def load_json():
    with open('archive.json', 'r') as archive:
        json_data = json.load(archive)
    with open('config.json', 'r') as config:
        json_data['config'] = json.load(config)
    return json_data


def gen_post_entry(files_directory, post_file, count, config):
    entrydict = dict()
    entrydict['title'] = post_file
    t = os.path.getmtime(files_directory + '/' + post_file)
    gmt = time.gmtime(t)
    entrydict['publish_date'] = time.strftime(config['date_format_string'], gmt)
    entrydict['ID'] = count
    entrydict['FNAME'] = post_file
    return entrydict


def clear_site(config):
    # remove the old verison of the site and recreate the folder
    shutil.rmtree(config['site_path'], ignore_errors=True)
    os.makedirs(config['site_path'], exist_ok=False)


def update_archive(config, json_data):
    # look for posts in config['post_path']
    # if it's not in the archive, add it
    archive_posts = json_data['posts']
    # os.walk yields a 3-tuple (dirpath, dirnames, filenames)
    step = next(os.walk(config['posts_path']))
    files_directory = step[0]
    files = step[2]

    # make sure all filenames are unique
    assert len(files) == len(set(files))

    count = len(archive_posts) # this becomes the added posts ID

    # build a dictionary of posts in archive where FNAME is key
    archive_postsdict = dict()
    for post in archive_posts:
        FNAME = post['FNAME']
        archive_postsdict[FNAME] = post

    # add posts not in the archive_posts
    posts_to_add = []
    for post_file in files:
        if post_file not in archive_postsdict:
            posts_to_add.append(post_file)

    # order by modification date
    # create a tuple of (m date, add_post)
    for i, add_post in enumerate(posts_to_add):
        mtime = os.path.getmtime(config['posts_path'] + '/' + add_post)
        posts_to_add[i] = (mtime, add_post)

    posts_to_add = sorted(posts_to_add, key=lambda add_post: add_post[0])
    # posts need to be displayed in reverse chronological order so reverse them.
    posts_to_add = reversed(posts_to_add)

    # generate post entrys for the posts being added to the archive
    for post_file in posts_to_add:
        post_file = post_file[1] # get just the file name from the tuple
        archive_posts.append(gen_post_entry(files_directory, post_file, count, config))
        count += 1

    # update the json_data with the updated list of posts
    json_data['posts'] = archive_posts

def load_content(config, post_fname):
    with open(config['posts_path'] + '/' + post_fname, 'r') as f:
        content = f.read()
    return content


def get_buttons(cur_page, post_count, pagination_count, button_count):
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

def build_archive_page(config, json_data):

    env = Environment(loader=PackageLoader(
                        config['site_path'], config['templates_path']))
    template = env.get_template(config['archive_template'])

    # build so many posts at a time based on pagination_count
    posts = copy.deepcopy(json_data['posts'])
    count = len(posts)
    pcount = config['archive_pagination_count'] # use a shorter name for readability
    blog_page_count = int(math.ceil(len(posts) / float(pcount)))
    for i in range(0, blog_page_count):
        page_posts = posts[(i * pcount): (i * pcount) + pcount]
        for j, post in enumerate(page_posts):
            post['link'] = '../blog/' + str(j + (i*pcount)) + '.html'
        buttons = get_buttons(i, count, config['archive_pagination_count'], config['archive_pagination_button_count'])
        # render the current page
        with open(config['site_path'] + '/archive/' + str(i) + '.html', 'w') as f:
            f.write(template.render(posts=page_posts, buttons=buttons,))


def build_site(config, json_data):
    # move static files over
    copy_tree('static', config['site_path'])
    shutil.copytree('css', config['site_path'] + '/css')
    shutil.copytree(config['templates_path'], config['site_path'] + '/templates')

    # create a folder to hold blog posts
    os.makedirs(config['site_path'] + '/blog')
    # create a folder to hold blog posts
    os.makedirs(config['site_path'] + '/archive')

    # create an __init__.py file so that jinja2 recognizes site_path as a module
    with open(config['site_path'] + '/__init__.py', 'w') as f:
        pass

    env = Environment(loader=PackageLoader(
                        config['site_path'], config['templates_path']))
    template = env.get_template(config['blog_template'])

    # build so many posts at a time based on pagination_count
    posts = copy.deepcopy(json_data['posts'])
    count = len(posts)
    for i in range(0, count):
        post = posts[i]
        post['content'] = markdown.markdown(load_content(config, post['FNAME']), extensions=['markdown.extensions.fenced_code'])
        # only show one post per page, so pass 1 as pagination_count
        buttons = get_buttons(i, count, 1, config['pagination_button_count'])
        # render the current page
        with open(config['site_path'] + '/blog/' + str(i) + '.html', 'w') as f:
            f.write(template.render(post=post, buttons=buttons))


def build():
    json_data = load_json()
    config = get_config(json_data)
    clear_site(config)
    update_archive(config, json_data)
    build_site(config, json_data)
    build_archive_page(config, json_data)
    write_changes(json_data)

build()
