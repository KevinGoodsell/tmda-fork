import copy

class Simple:
  def __init__(self, Text):
    self.Text = Text
  def __repr__(self):
    return self.Text

# Constants
Reverse    = { "R": "L", "L": "R" }
Down       = Simple("<td align=center><img src=down.gif></td>\n")
Left       = Simple("<td><img src=left.gif></td>\n")
Right      = Simple("<td><img src=right.gif></td>\n")
RightMerge = Simple("<td class=rm></td>\n")
LeftMerge  = Simple("<td class=lm></td>\n")
RightDown  = Simple("<td class=rd></td>\n")
LeftDown   = Simple("<td class=ld></td>\n")
Horz       = Simple("<td class=horz></td>\n")
Vert       = Simple("<td class=vert></td>\n")

class Target:
  "Targets are destinations (actions)."
  def __init__(self, Dest):
    "Constructor"
    self.Dest = Dest
    
  def __repr__(self):
    "Representation."
    return "<td><table class=Target width=100 height=50><tr><td>%s</td></tr></table></td>\n" % self.Dest
  
class Node:
  "Nodes are tests (conditionals)."
  
  Dir    = "R"  # Right or Left
  Direct = 1    # Direct attachment or not
  Closed = 0    # Node is bottled up
  Next   = None # Next node below
  Prev   = None # Previous node above

  def __init__(self, Cond, Dest):
    "Constructor."
    self.Cond = Cond
    self.Dest = Dest
  
  def __repr__(self):
    "Print out contents."
    return "<td><table class=Condition width=100 height=50><tr><td>%s</td></tr></table></td>\n" % self.Cond
      
  def Targets(self):
    "Returns the total score from this point down."
    if self.Next: return self.Direct + self.Next.Targets()
    else:         return self.Direct
  
  def Top(self):
    "Return the first node."
    if self.Prev: return self.Prev.Top()
    else:         return self
  
  def Bottom(self):
    "Return the last node."
    if self.Next: return self.Next.Bottom()
    else:         return self
  
  def ScanUp(self, N):
    "Return the lowest matching node."
    RetVal = None
    if (self.Dest == N.Dest):
      return self
    if self.Prev:
      return self.Prev.ScanUp(N)
    else:
      return None
      
  def Backup(self):
    "Make a backup of this node and nodes below."
    self.Save = self.Dir, self.Direct, self.Closed
    if self.Next: self.Next.Backup()
  
  def Restore(self):
    "Restore from backup, this node and below."
    self.Dir, self.Direct, self.Closed = self.Save
    if self.Next: self.Next.Restore()
  
  def CloseOff(self, StopAt):
    "Close off trapped nodes up to StopAt."
    if self == StopAt:
      return
    if self.Dir == StopAt.Dir:
      self.Closed = 1
    self.Prev.CloseOff(StopAt)
  
  def TestCollide(self, Targets):
    "Test to see if path from self collides with other targets."
    for Target in Targets:
      if Target == self.Dest:
        continue
      if Target.X != self.Dest.X:
        continue
      if Target.Y < self.Y:
        continue
      if Target.Y > self.Dest.Y:
        continue
      return Target
    return None
  
  def Recalc(self):
    "Recalculate Direct and Closed of this node and below."
    self.Closed = 0
    self.Direct = 1
    if self.Prev:
      Curr = self.Prev.ScanUp(self)
      if Curr:
        if (Curr.Dir == self.Dir) and not Curr.Closed:
          Curr.Direct = 0

          # Did we close anything off?
          self.Prev.CloseOff(Curr)
    if self.Next:
      self.Next.Recalc()
  
  def Append(self, N):
    "Add node to bottom of list."
    # Find bottom of stack
    Bottom = self.Bottom()
    
    # Add node to bottom
    Bottom.Next = N
    N.Prev = Bottom
    N.X = Bottom.X
    N.Y = Bottom.Y + 1
    
    # Scan back up the stack to see if we can combine
    Curr = Bottom.ScanUp(N)
    if Curr:
      if not Curr.Closed:
        Curr.Direct = 0
        N.Dir = Curr.Dir
        
        # Did we close anything off?
        Bottom.CloseOff(Curr)
      else:
        # We can't merge to closed node.  Will try reversing node @ Curr.
        Top = self.Top()
        CurrScore = Top.Targets()
        
        # Make a backup in case this doesn't help
        Top.Backup()
        
        # Try to merge with closed once it is reversed
        N.Dir = Reverse[Curr.Dir]
        
        # Go up the list from Curr.  Will need to reverse it and all nodes
        # that lead to the same destination.
        Temp = Curr
        while 1:
          Temp.Dir = Reverse[Temp.Dir]
          Temp = Temp.ScanUp(N)
          if not Temp or Temp.Direct:
            break
  
        # Recalc which nodes are closed off
        Top.Recalc()
            
        # Restore from backup if we didn't help any
        if Top.Targets() >= CurrScore:
          # Restore from backup
          Top.Restore()

class Diagram:
  Top = None
  
  def __repr__(self):
    RetVal = "<table border=0 cellspacing=0 cellpadding=0 align=center>\n"
    for Row in self.Array:
      RetVal += "<tr>\n"
      for Cell in Row:
        if Cell:
          RetVal += repr(Cell)
        else:
          RetVal += "<td></td>\n"
      RetVal += "</tr>\n"
    RetVal += "</table>\n"
    return RetVal
    
  def Append(self, N):
    if self.Top:
      self.Top.Append(N)
    else:
      self.Top = N
      self.Top.X = 0
      self.Top.Y = 0
  
  def _UniqTargets_(self):
    """Duplicate targets as needed so that each Direct connect is unique.
  
Compile a list of targets used in Targets."""
    Curr = self.Top.Bottom()
    self.Targets = []
    while Curr:
      # Find direct connected targets
      if Curr.Direct:
        Dest = Curr.Dest
        
        # Make a copy and keep in the list
        Curr.Dest = copy.copy(Dest)
        self.Targets.append(Curr.Dest)
        Curr.Dest.Y = Curr.Y
        if Curr.Dir == "L":
          Curr.Dest.X = Curr.X - 1
        else:
          Curr.Dest.X = Curr.X + 1
        
        # Find all others connected to it and update them
        Temp = Curr.Prev
        while Temp:
          if Temp.Dest == Dest:
            if Temp.Direct:
              break
            else:
              Temp.Dest = Curr.Dest
          Temp = Temp.Prev
    
      Curr = Curr.Prev
  
  def _FixCollisions_(self):
    "Scoot targets as needed to avoid crosses."
    Curr = self.Top
    while Curr:
      if Curr.TestCollide(self.Targets):
        if Curr.Dir == "L":
          Curr.Dest.X -= 1
        else:
          Curr.Dest.X += 1
        return Curr
      Curr = Curr.Next
    return None
  
  def _FindMinMax_(self):
    "Find size of diagram."
    MinX = 0
    MaxX = 0
    MaxY = 0
    for Target in self.Targets:
      if Target.X < MinX:
        MinX = Target.X
      if Target.X > MaxX:
        MaxX = Target.X
      if Target.Y > MaxY:
        MaxY = Target.Y
    return MinX, MaxX, MaxY
  
  def _MakeArray_(self):
    "From a compiled set of targets and nodes, make the array."
    
    # Create a blank array
    MinX, MaxX, MaxY = self._FindMinMax_()
    self.Array = []
    for y in range(MaxY * 2 + 1):
      self.Array.append([])
      for x in range((MaxX - MinX) * 2 + 1):
        self.Array[y].append(None)
    
    # Put targets in array
    for Target in self.Targets:
      self.Array[Target.Y * 2][(Target.X - MinX) * 2] = Target
    
    # Put nodes and links in array
    Curr = self.Top
    while Curr:
      # Place node
      self.Array[Curr.Y * 2][(Curr.X - MinX) * 2] = Curr
      
      # Arrow?
      if Curr.Next:
        self.Array[Curr.Y * 2 + 1][(Curr.X - MinX) * 2] = Down
      
      if Curr.Dir == "R":
        # Draw horizontal connection
        for x in range((Curr.X - MinX) * 2 + 1, (Curr.Dest.X - MinX) * 2):
          self.Array[Curr.Y * 2][x] = Horz
        
        # Arrow or "T"
        if Curr.Y == Curr.Dest.Y:
          self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2 - 1] = Right
        else:
          if self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2]:
            self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2] = RightMerge
          else:
            self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2] = RightDown

      else:
        # Draw horizontal connection
        for x in range((Curr.Dest.X - MinX) * 2 + 1, (Curr.X - MinX) * 2):
          self.Array[Curr.Y * 2][x] = Horz
        
        # Arrow or "T"
        if Curr.Y == Curr.Dest.Y:
          self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2 + 1] = Left
        else:
          if self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2]:
            self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2] = LeftMerge
          else:
            self.Array[Curr.Y * 2][(Curr.Dest.X - MinX) * 2] = LeftDown

      if Curr.Y != Curr.Dest.Y:
        # Draw a vertical connection
        for y in range(Curr.Y * 2 + 1, Curr.Dest.Y * 2 - 1):
          self.Array[y][(Curr.Dest.X - MinX) * 2] = Vert
        
        # Arrow
        self.Array[Curr.Dest.Y * 2 - 1][(Curr.Dest.X - MinX) * 2] = Down

      Curr = Curr.Next

  def Compile(self):
    self._UniqTargets_()
    while self._FixCollisions_():
      pass
    self._MakeArray_()

#A, B, C, D = Target("A"), Target("B"), Target("C"), Target("D")
Reject, Accept = Target("Reject"), Target("Accept")
Dgram = Diagram()
#for a in [A,B,D,C,D,A,B,C,B,A,A,C,C,B,D,A,D]: Dgram.Append(Node("[%s]" % a.Dest, a))
Dgram.Append(Node("from<br><span class=Filename>blacklist</span>", Reject))
Dgram.Append(Node("from<br><span class=Filename>whitelist</span>", Accept))
Dgram.Append(Node("from<br><span class=Filename>confirmed</span>", Accept))

Dgram.Compile()
print Dgram
#print Dgram.Top
