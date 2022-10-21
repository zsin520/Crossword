#! /usr/bin/env python3

import sys

from crossword import *
from operator import itemgetter

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        print(assignment)
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for key in self.domains.keys():
            for val in self.crossword.words.copy():
                if not key.length == len(val):
                    self.domains[key].remove(val)
    
        
    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised=False
        if self.crossword.overlaps[x,y] == None:
            return revised 
        i,j=self.crossword.overlaps[x,y]
        for xval in self.domains[x].copy():
            if not any(D[j] == xval[i] for D in self.domains[y]):
                self.domains[x].remove(xval)
                revised=True
        return revised 
        

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        def queue(x,y):
            arcs.append(tuple((x,y)))
        def dequeue():
            pair= arcs[0]
            arcs.pop(0)
            return pair
        
        if arcs==None:
            arcs=[x for x in self.crossword.overlaps.keys()]

        while len(arcs) != 0:
            x,y=dequeue()
            if self.revise(x,y):
                if len(self.domains[x]) == 0:
                    return False
                for var in self.crossword.neighbors(x):
                    if var != y:
                        queue(x,var)

        return True 
            

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        complete=False
        for var in self.crossword.variables:
            if var not in assignment:
                return complete
        return True 

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        consistent=False
        for key in assignment:
            var=assignment[key]
            if key.length != len(var):
                return consistent 
            for chk in assignment:
                if key == chk:
                    continue
                elif assignment[key] == assignment[chk]:
                    return consistent 
            for nbr in self.crossword.neighbors(key):
                if nbr not in assignment:
                    continue
                i,j=self.crossword.overlaps[key,nbr]
                if var[i] != assignment[nbr][j]:
                    return consistent
        return True 
                

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        if len(self.domains[var]) == 1:
            return list(self.domains[var])

        dvar=[]
        temp_dic={}
        for val in self.domains[var]:
            temp_dic[val]=0
            for nbr in self.crossword.neighbors(var):
                if nbr in assignment:
                    continue
                i,j=self.crossword.overlaps[var,nbr]
                for nbr_val in self.domains[nbr]:
                    if val[i] != nbr_val[j]:
                        temp_dic[val]+=1
        return_dic=sorted(temp_dic.items(),key=lambda item:item[1])
        for key in return_dic:
            dvar.append(key[0])

        return dvar

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        var_list=[]
        for var in self.crossword.variables:
            if var not in assignment:
                temp_list=[]
                temp_list.append(var)
                temp_list.append(len(self.domains[var]))
                temp_list.append(1/len(self.crossword.neighbors(var)))
                var_list.append(temp_list)
        if len(var_list)==1:
            return var_list[0][0]
        
        var_list.sort(key=itemgetter(1,2))
        return var_list[0][0]
    
    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var=self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var,assignment):
            assignment[var]=value
            if self.consistent(assignment):
                result=self.backtrack(assignment)
                if result:
                    return result
            assignment.pop(var)
        return None 


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
