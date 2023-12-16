#!/usr/bin/env python3

import argparse
import hashlib
import os
import fnmatch
import shutil


def calculate_file_sha1(path, max_hash_size):
    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        if max_hash_size > 0:
            sha1.update(f.read(max_hash_size))
            return sha1.hexdigest()

        for chunk in iter(lambda: f.read(16384), b''):
            sha1.update(chunk)

    return sha1.hexdigest()


def generate_state(top_dir, excludes, max_hash_size):
    for root, dirs, files in os.walk(top_dir):
        for file in files:
            path = os.path.join(root, file)
            if any(fnmatch.fnmatch(path, os.path.join(root, exclude)) for exclude in excludes):
                continue

            checksum = calculate_file_sha1(path, max_hash_size)
            yield path[len(top_dir) + 1:], checksum


def freeze(source_dir, state_file, excludes, max_hash_size):
    with open(state_file, 'w') as f:
        state_dict = get_state_from_sources(source_dir, excludes, max_hash_size)
        for key, value in state_dict.items():
            f.write("{value}  {key}\n".format(key=key, value=value))


def get_state_from_sources(source_dir, excludes, max_hash_size):
    state_dict = {}
    for path, checksum in generate_state(source_dir, excludes, max_hash_size):
        state_dict[path] = checksum

    return state_dict


def get_state_from_file(state_file):
    state_dict = {}
    with open(state_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            tokens = line.split("  ", 2)
            state_dict[tokens[1]] = tokens[0]

    return state_dict


def generate_diff(source_dir, state_path, excludes, max_hash_size):
    diff_attrs = {'add': [], 'delete': [], 'rename': []}
    state_origin = get_state_from_file(state_path)
    hash_to_file_origin = {v: k for k, v in state_origin.items()}
    state_now = get_state_from_sources(source_dir, excludes, max_hash_size)
    hash_to_file_now = {v: k for k, v in state_now.items()}
    for path, checksum in state_origin.items():
        if any(fnmatch.fnmatch(path, os.path.join(source_dir, exclude)) for exclude in excludes):
            continue

        if path not in state_now:
            if checksum in hash_to_file_now:
                diff_attrs['rename'].append((path, hash_to_file_now[checksum]))

            else:
                diff_attrs['delete'].append(path)

        elif checksum != state_now[path]:
            diff_attrs['add'].append(path)

    for path, checksum in state_now.items():
        if any(fnmatch.fnmatch(path, os.path.join(source_dir, exclude)) for exclude in excludes):
            continue

        if path not in state_origin:
            diff_attrs['add'].append(path)

    return diff_attrs


def diff(source_dir, state_path, destination, excludes, max_hash_size):
    diff_attrs = generate_diff(source_dir, state_path, excludes, max_hash_size)
    os.makedirs(destination, exist_ok=True)
    state_file = os.path.join(destination, '.delete')
    with open(state_file, 'w') as fs:
        for dpath in diff_attrs['delete']:
            fs.write(dpath + '\n')

    state_file = os.path.join(destination, '.rename')
    with open(state_file, 'w') as fs:
        for rpath in diff_attrs['rename']:
            fs.write('{} -> {}'.format(*rpath) + '\n')

    add_dir = os.path.join(destination, '.add')
    for relapath in diff_attrs['add']:
        spath = os.path.join(source_dir, relapath)
        dpath = os.path.join(add_dir, relapath)
        os.makedirs(os.path.dirname(dpath), exist_ok=True)
        shutil.copy2(spath, dpath, follow_symlinks=True)


def patch(diff_dir, destination, excludes, delete):
    if delete is True:
        state_file = os.path.join(diff_dir, '.delete')
        with open(state_file, 'r') as fs:
            lines = fs.readlines()
            for line in lines:
                line = line.strip()
                dpath = os.path.join(destination, line)
                if os.path.exists(dpath):
                    os.unlink(dpath)

    state_file = os.path.join(diff_dir, '.rename')
    with open(state_file, 'r') as fs:
        lines = fs.readlines()
        for line in lines:
            line = line.strip()
            names = line.split(' -> ')
            paths = [os.path.join(destination, names[x]) for x in range(2)]
            os.makedirs(os.path.dirname(paths[1]), exist_ok=True)
            os.rename(paths[0], paths[1])

    add_dir = os.path.join(diff_dir, '.add')
    for root, dirs, files in os.walk(add_dir):
        for name in files:
            path = os.path.join(root, name)
            relapath = path[len(add_dir) + 1:]
            dpath = os.path.join(destination, relapath)
            os.makedirs(os.path.dirname(dpath), exist_ok=True)
            shutil.copy2(path, dpath, follow_symlinks=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Another Offline File Sync Tool')
    parser.add_argument("-d", "--delete", action='store_true', default=False, help="delete files from destination")
    parser.add_argument("-e", "--excludes", dest="excludes", nargs='*', default=[], help="exclude glob patterns")
    parser.add_argument("-M", "--max-hash-size", dest="max_hash_size", type=int, default=0, help="max hash size")
    parser.add_argument("-c", "--command", dest="command", choices=["freeze", "diff", "patch"], help="command [freeze/diff/patch]")
    parser.add_argument("dirs", type=str, nargs='+', help="directory list")
    args = parser.parse_args()

    if args.command == "freeze":
        freeze(args.dirs[0], args.dirs[1], args.excludes, args.max_hash_size)

    elif args.command == "diff":
        diff(args.dirs[0], args.dirs[1], args.dirs[2], args.excludes, args.max_hash_size)

    elif args.command == "patch":
        patch(args.dirs[0], args.dirs[1], args.excludes, args.delete)
