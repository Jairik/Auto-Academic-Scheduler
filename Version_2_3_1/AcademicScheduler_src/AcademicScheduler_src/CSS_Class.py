#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 15:40:17 2021

Revised: 8/6/2021

@author: Don Spickler

This script simply stores the global stylesheeting for the program.  The getCSS
function returns the stylesheet string.

"""


class appcss:
    def __init__(self):
        super().__init__()
        self.css = """
            QMenu::separator { 
                background-color: #BBBBBB; 
                height: 1px; 
                margin: 3px 5px 3px 5px;
            }
                
        """

    def getCSS(self) -> str:
        return self.css
