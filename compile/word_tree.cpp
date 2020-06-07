/* 
    Sets up a tree of available words along with how frequent they are.
    It may have been better to use binary search, but it's a bit late for
        that, no?
    Compile to libWordTree.dylib with -std=c++11
*/

#include <iostream>
#include <fstream>
#include <string>
#include <tuple>
#include <vector>
#include <algorithm>
#include <stdlib.h>

using namespace std;

struct letter_node {
    int freq; // -1 if not valid
    vector<struct letter_node> next;
    char c;
};

int lines = 0;
int max_lines;

/*
    Helper functions
*/

string c_string_to_cpp (char *str) {
    // Assumes str is null-terminated
    string return_string;
    for (int i=0; str[i]!='\0'; i++) {
        return_string.push_back(str[i]);
    }
    return return_string;
}

bool a_lessthan_b(tuple<string, int> a, tuple<string, int> b) {
    return (get<1>(a) < get<1>(b));
}

/*
    Tree Setup
*/

struct letter_node tree_start;

void add_branch(struct letter_node *root, char c, int *freq, string cur_string, string *target_string, ifstream *fin) {
    /* 
    Parameters:
     * root - The root of the tree, must be initialized before the call
     * c - character for the next node
     * cur_string - current string being tracked, pass "" as it is only used for recursion
     * target_string - string we want to get to. Must be initialized before the call
     * fin - pointer to the ifstream the data is coming from
    Follows algorithm:
     * If this new branch is just a piece of the target string, create a new branch moving towards the target string.
     * If this new branch is not a substring, remove the last character of current string and go back
     * If this new branch is the target string, get the next set of data in fin and continue.
    */
   
    struct letter_node new_node;
    new_node.c = c;
    new_node.freq = -1;
    
    cur_string.push_back(c);
    
    if (cur_string.compare(*target_string) == 0) {
        // We found it. Set the frequency and target string, and start the next search.
        new_node.freq = *freq;

        *fin >> *target_string;
        *fin >> *freq;
        lines+=1;
    }
    //cout << 4 << endl;
    while (target_string->substr(0, cur_string.length()).compare(cur_string) == 0) {
        // While current string is a substring
        add_branch(&new_node, (*target_string)[cur_string.length()], freq, cur_string, target_string, fin);
    }

    // Add to root
    root->next.push_back(new_node);
}

void create_tree(string freq_file) {
    /* Base function for creating the tree */
    tree_start.freq = -1;
    tree_start.c = (char) 0;

    ifstream fin(freq_file);
    fin >> max_lines;
    max_lines -= 10;
    
    string *start_target = new string();
    int *start_freq = new int();
    
    fin >> *start_target;
    fin >> *start_freq;
    
    lines = 1;

    while (lines < max_lines) {
        add_branch(&tree_start, (*start_target)[0], start_freq, "", start_target, &fin);
    }
}

/* 
    Getters in c++ 
     * All getters convert data to a c-compatible format for easy usage in ctypes
*/

void get_autocomplete_recursive(struct letter_node node, string current_string, string prefix, vector<tuple<string, int>> *options, int n) {
    /* 
    Autocomplete with recursive 
    Parameters:
     * node - current node being checked
     * current_string - current string being used
     * prefix - prefix for valid return string
     * options - return buffer
     * n - length of vector (avoids an unnecessarily long sort())
    */
    current_string.push_back(node.c);
    if (current_string.length() >= prefix.length()) {
        // Prefix is a substring
        // Check if this node is valid
        if (node.freq != -1) {
            // Valid node.
            options->push_back(make_tuple(current_string, node.freq));
            if (options->size() > n) {
                auto largest = options->begin();
                for (auto it=options->begin(); it!=options->end(); ++it) {
                    if (a_lessthan_b(*largest, *it)) {
                        largest = it;
                    }
                }
                options->erase(largest);
            }
        }
        // Now check child nodes
        for (auto it=node.next.begin(); it != node.next.end(); ++it) {
            get_autocomplete_recursive(*it, current_string, prefix, options, n);
        }
    }
    else {
        // Prefix is not substring
        for (auto it=node.next.begin(); it != node.next.end(); ++it) {
            if (it->c == prefix[current_string.length()]) {
                get_autocomplete_recursive(*it, current_string, prefix, options, n);
            }
        }
    }
}

extern "C" { // 

char *get_autocomplete(char *prefix, int n) {
    /*
    Returns: 
     * A string containing the n best autocompletes for the prefix
     * The string will be separated by newline characters
    Starts by constructing such a string using std::string then converting it to a c string.
    */

    string cpp_prefix = c_string_to_cpp(prefix);

    vector<tuple<string, int>> options;
    // Find the start letter and it's smooth sailing
    for (auto it=tree_start.next.begin(); it!=tree_start.next.end(); ++it) {
        if (it->c == prefix[0]) {
            get_autocomplete_recursive(*it, "", cpp_prefix, &options, n);
        }
    }
    sort (options.begin(), options.end(), a_lessthan_b);
    // Make sure n isn't too big
    if (n > options.size()) {
        n = options.size();
    }
    // Construct the return string
    string return_stringcpp;
    for (int i=0; i<n; i++) {
        string thing = get<0>(options[i]);
        return_stringcpp += thing + " ";
    }
    char *return_string;
    return_string = (char*)malloc(sizeof(char)*return_stringcpp.length()); // Remember to free()!
    for (int i=0; i<return_stringcpp.length(); i++) {
        return_string[i] = return_stringcpp[i];
    }
    return_string[return_stringcpp.length()-1] = '\0';
    //cout << return_string << endl;
    return return_string;
}

void set_tree(char *filename) {
    // Sets up the tree. Call this before anything else in the library, or risk a possible segfault
    string cpp_string_name;
    for (int i=0; filename[i] != '\0'; i++) {
        cpp_string_name.push_back(filename[i]);
    }
    
    create_tree(cpp_string_name);
}

} // End extern "C"
