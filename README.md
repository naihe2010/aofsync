aofsync - Alf's offline file sync tool

# Description

aofsync is tool for backup files offline and increasingly.

# Usage

aofsync supports three commands: 'freeze', 'diff', and 'patch'.

Here's the workflow:

1. We have two identical directories: the source and the destination. These directories are not on the same host.
2. We intend to work on the source directory. Therefore, we freeze the source to a state file by executing the following command:
> aofsync -c freeze ./source ./source.state

3. After that, we can make changes to the source directory. We can add, delete, or modify content as needed.
4. After a while, we want to merge the changes to the destination directory on another host. So, we execute the following two steps:
> aofsync -c diff ./source ./source.state ./diff

Now, we have a ./diff directory, which only contains the increments from the source. We copy it to the host that contains the destination directory and execute:

> aofsync -c patch ./diff ./dest

Now, the destination directory will be identical to the source directory.

# Other Options

+ -d --delete delete files from destination
+ -e --excludes exclude glob pattern, like: -e *.svn *.git
+ -M --max-hash-size max hash size, default is 0

# Support Platforms

+ GNU/Linux
+ Windows 10 or later

# Develop Dependencies

+ Python3
+ poetry