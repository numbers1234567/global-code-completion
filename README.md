# global-code-completion
As github users, we may all be familiar with IDEs and code completion. But what if we could do that for every application, from word documents to to-do lists? This program intends to implement such an idea.

This is a bit buggy for now, but that's being worked on. An important thing to note is that this only works on Mac OS X, and requires you to run as root due to the keyboard module. 

If you are a really fast typer (like I am) and this program doesn't really help, you can compile your own word list by editing word_list.txt and using longer words (>7 characters). word_list.txt has to be ordered alphabetically, with the first line being how many words there are, with the number beside each word being their frequency ranking.
