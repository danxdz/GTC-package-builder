from steptools import step

# Read a STEP-NC file
DESIGN = step.open_project("examples/tst.stp")

GEN = step.Generate()
GEN.set_style("fanuc")   # use Fanuc style

# expand export_cncfile() and print to terminal instead of file
CUR = step.Adaptive()      # walks over the process
CUR.start_project(DESIGN)
CUR.set_wanted_all()
GS = step.GenerateState()  # keeps current state of codes

print(CUR.get_frame_type(2))