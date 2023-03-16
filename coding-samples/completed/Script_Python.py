#!/usr/bin/env python3
import os
import sys
import time
import shutil
import subprocess

class OpticalWriteTest:
    def __init__(self):
        self.tmp_dir = '/tmp/optical-test'
        self.iso_name = 'optical-test.iso'
        self.sample_file_path = '/usr/share/example-content/'
        self.sample_file = 'Ubuntu_Free_Culture_Showcase'
        self.md5sum_file = 'optical_test.md5'
        self.start_dir = os.getcwd()

    def create_working_dirs(self):
        # First, create the temp dir and cd there
        print("Creating Temp directory and moving there ...")
        try:
            os.mkdir(self.tmp_dir)
            os.chdir(self.tmp_dir)
        except:
            self.failed("Failed to create working directories")
        cwd = os.getcwd()
        print(f"Now working in {cwd} ...")

    def get_sample_data(self):
        # Get our sample files
        print(f"Getting sample files from {self.sample_file_path} ...")
        full_path = os.path.join(self.sample_file_path, self.sample_file)
        try:
            shutil.copyfile(full_path, self.tmp_dir)
        except:
            self.failed("Failed to copy sample data")
            
    def generate_md5(self):
        # Generate the md5sum
        print("Generating md5sums of sample files ...")
        cwd = os.getcwd()
        md5sum_path = os.path.join(self.tmp_dir, self.md5sum_file)
        md5sum_cmd = f'md5sum -- * > {md5sum_path}'
        try:
            subprocess.run([md5sum_cmd])
            # Check the sums for paranoia sake
            self.check_md5(md5sum_path)
        except:
            self.failed("Failed to generate initial md5")
        
        try:
            os.chdir(cwd)
        except:
            sys.exit(1)

    def check_md5(self, file):
        print("Checking md5sums ...")
        try:
            check_md5_cmd = f"md5sum -c {file}"
            subprocess.run([check_md5_cmd])
        except:
            self.failed("Failed to generate initial md5")

    def generate_iso(self):
        # Generate ISO image
        print("Creating ISO Image ...")
        try:
            geniso_cmd =('genisoimage -input-charset UTF-8 -r -J '
                        f'-o {self.iso_name} {self.sample_file}')
            subprocess.run([geniso_cmd])
        except:
            self.failed("Failed to create ISO image")

    def burn_iso(self):
        # Burn the ISO with the appropriate tool
        print("Sleeping 10 seconds in case drive is not yet ready ...")
        time.sleep(10)
        print("Beginning image burn ...")
        if optical_type == 'cd':
            burn_iso_cmd = f'wodim -eject dev={optical_drive} {self.iso_name}'
        elif optical_type == 'dvd' or optical_type == 'bd':
            burn_iso_cmd = ('growisofs -dvd-compat '
                           f'-Z "{optical_drive}={self.iso_name}"')
        else:
            print(f"Invalid type specified {optical_type}")
            sys.exit(1)

        try:
            subprocess.run([burn_iso_cmd])
        except:
            self.failed("Failed to burn ISO image")

    def cleanup(self):
        print ("Moving back to original location")
        os.chdir(self.start_dir)
        cwd = os.getcwd()
        print(f"Now residing in {cwd}")
        print("Cleaning up ...")
        umount_cmd = f'umount {self.mount_pt}'
        eject_cmd = f'eject {optical_drive}'
        try:
            subprocess.run([umount_cmd])
            shutil.rmtree(self.tmp_dir)
            print("Ejecting spent media ...")
            subprocess.run([eject_cmd])
        except:
            self.failed("Failed to clean up")
        
    def failed(self, message):
        print(message)
        print("Attempting to clean up ...")
        self.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    if os.path.exists(sys.argv[1]):
        optical_drive = os.path.realpath(sys.argv[1])
    else:
        optical_drive='/dev/sr0'

    if len(sys.argv) > 2 and sys.argv[2]:
        optical_type = sys.argv[2]
    else:
        optical_type = "cd"
    
    test = OpticalWriteTest()
    #test.create_working_dirs()
    #test.get_sample_data()
    #test.generate_md5()
    #test.generate_iso()
    #test.burn_iso()
    #test.cleanup()
    sys.exit(0)