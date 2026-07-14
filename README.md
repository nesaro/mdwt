# mdwt

markdown wiki tools. A collection of functions that I have used or use for my personal PKM.

The main requirement is the cog library, and I call these functions inside
blocks in the markdown, similar to org-mode babel
e.g.:

```
`cog from tools import *;print_image("/path/to/image.jpg") cog`

`end`
```

The I have a vim shortcut to generate the output. In my .vimrc:

```
nmap <F10> :!cog --markers '`cog cog` `end`' -r %:p<CR>:e<CR>
```
