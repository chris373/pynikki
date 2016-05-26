import os
import math
from collections import namedtuple
from jinja2 import Environment, PackageLoader
import json
import time
import copy

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
    return json_data


def clear_site(config): # remove blog files so it can be rebuilt
    # os.walk yields a 3-tuple (dirpath, dirnames, filenames)
    step = next(os.walk(config['site_path'] + '/' + 'blog'))
    files_directory = step[0]
    files = step[2]
    html_files = [
        files_directory + '/' + f
        for f in files if get_extension(f) == 'html'
    ]
    for f in html_files:
        os.remove(f)

def gen_post_entry(files_directory, post_file, count):
    entrydict = dict()
    entrydict['title'] = post_file
    entrydict['publish_date'] = os.path.getmtime(
                                files_directory + '/' + post_file)
    entrydict['ID'] = count
    entrydict['FNAME'] = post_file
    return entrydict


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

    count = len(archive_posts) # this becomes the added post's ID

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

    # generate post entrys for the posts being added to the archive
    for post_file in posts_to_add:
        post_file = post_file[1] # get just the file name from the tuple
        archive_posts.append(gen_post_entry(files_directory, post_file, count))
        count += 1

    # update the json_data with the updated list of posts
    json_data['posts'] = archive_posts

def load_content(config, post_fname):
    with open(config['posts_path'] + '/' + post_fname, 'r') as f:
        content = f.read()
    return content


def get_buttons(cur_page, post_count, config):
    # generate numbers, active, link
    # first, back, numbered, forward, last
    page_count = int(math.ceil(post_count / float(config['pagination_count'])))
    side = int(math.floor(config['pagination_button_count'] / 2.0))
    buttons = [b for b in range(cur_page - side, cur_page + side + 1)]
    append_count = len([b for b in buttons if b < 0])
    prepend_count = len([b for b in buttons if b >= page_count])
    for i in range(0, append_count):
        buttons.pop(0)
        buttons.append(cur_page + i + side + 1)
    for i in range(0, prepend_count):
        buttons.pop()
        buttons.insert(0, cur_page - i - side - 1)

    button_dicts = []
    for button in buttons:
        if button == cur_page:
            button_dicts.append({'active': 'active', 'number': str(cur_page),
                                'link': '#'})
        else:
            button_dicts.append({'active': 'disabled', 'number': str(button),
                                'link': str(button) + '.html'})

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


def build_site(config, json_data):
    # load template
    env = Environment(loader=PackageLoader(
                        config['site_path'], config['templates_path']))
    template = env.get_template(config['blog_template'])

    # build so many posts at a time based on pagination_count
    count = len(json_data['posts'])
    posts = copy.deepcopy(json_data['posts'])
    blog_page_count = int(math.ceil(len(posts) / float(config['pagination_count'])))
    pcount = config['pagination_count'] # use a shorter name for readability
    for i in range(0, blog_page_count):
        page_posts = posts[(i * pcount): (i * pcount) + pcount]
        for j, post in enumerate(page_posts):
            page_posts[j]['content'] = load_content(config, post['FNAME'])
        buttons = get_buttons(i, count, config)
        # render the current page
        with open(config['site_path'] + '/blog/' + str(i) + '.html', 'w') as f:
            f.write(template.render(posts=page_posts, buttons=buttons))


def build():
    json_data = load_json()
    config = get_config(json_data)
    clear_site(config)
    update_archive(config, json_data)
    build_site(config, json_data)
    write_changes(json_data)

build()
