from steputils import p21

FNAME = "step_test.stp"

# Create a new STEP-file:
stepfile = p21.new_step_file()

# Create a new data section:
data = stepfile.new_data_section()

# Add entity instances to data section:
data.add(p21.simple_instance('#1', name='APPLICATION', params=('MyApp', 'v1.0')))

# Set required header entities:
stepfile.header.set_file_description(('Example STEP file', 'v1.0'))
stepfile.header.set_file_name(name=FNAME, organization=('me', 'myself'), autorization='me')
stepfile.header.set_file_schema(('NONE',))

# Write STEP-file to file system:
stepfile.save(FNAME)

# Read an existing file from file system:
try:
    stepfile = p21.readfile(FNAME)
except IOError as e:
    print(str(e))
except ParseError as e:
    # Invalid STEP-file
    print(str(e))
else:
    print(f'File {FNAME} is a valid STEP-file')

qsd = stepfile.get("#1")

print(qsd)