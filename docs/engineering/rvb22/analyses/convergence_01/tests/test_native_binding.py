import copy, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_binding import content_hash
class BindingTests(unittest.TestCase):
    def setUp(self):
        self.board = ["kicad_pcb", ["generator","pcbnew"], ["generator_version","9.0"],
            ["footprint","TEST",["property","MPN","A",["uuid","p"]],
            ["fp_rect",["start",0,0],["end",1,1],["layer","B.CrtYd"],["uuid","f"]],
            ["pad","1","smd","rect",["at",0,0],["net",30,"GND"],["uuid","pad"]]],
            ["segment",["start",1,2],["end",3,4],["layer","F.Cu"],["uuid","s"]],
            ["zone",["net",30],["polygon",["pts",["xy",0,0],["xy",2,0],["xy",2,2]]],
             ["filled_polygon",["layer","In1.Cu"],["pts",["xy",1,1]]]],
            ["via",["at",2,2],["drill",0.2],["uuid","v"]]]
    def change(self,path,value,same=False):
        other=copy.deepcopy(self.board);node=other
        for k in path[:-1]:node=node[k]
        node[path[-1]]=value
        self.assertEqual(content_hash(self.board)==content_hash(other),same)
    def test_generator(self):self.change([1,1],"pcbnew-refill",True)
    def test_generator_version(self):self.change([2,1],"9.0.9",True)
    def test_top_level_record_order(self):
        other=copy.deepcopy(self.board);other[3:]=reversed(other[3:])
        self.assertEqual(content_hash(self.board),content_hash(other))
    def test_property_id(self):self.change([3,2,3,1],"new",True)
    def test_courtyard_id(self):self.change([3,3,-1,1],"new",True)
    def test_mpn(self):self.change([3,2,2],"B")
    def test_courtyard_geometry(self):self.change([3,3,1,1],.1)
    def test_pad_uuid(self):self.change([3,4,-1,1],"new")
    def test_pad_net(self):self.change([3,4,-2,1],31)
    def test_segment_geometry(self):self.change([4,1,1],1.1)
    def test_zone_outline(self):self.change([5,2,1,1,1],.1)
    def test_regenerated_filled_copper(self):self.change([5,3,2,1,1],1.1,True)
    def test_drill(self):self.change([6,2,1],.3)
if __name__=="__main__":unittest.main()
