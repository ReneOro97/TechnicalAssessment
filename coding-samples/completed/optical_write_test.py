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
        source = os.path.join(self.sample_file_path, self.sample_file)
        destination = self.tmp_dir
        try:
            shutil.copytree(source, destination)
        except:
            self.failed("Failed to copy sample data")
            
    def generate_md5(self):
        # Generate the md5sum
        print("Generating md5sums of sample files ...")
        cwd = os.getcwd()
        try:
            os.chdir(self.sample_file)
            md5sum_path = os.path.join(self.tmp_dir, self.md5sum_file)
            md5sum_cmd = f'md5sum -- * > {md5sum_path}'
            subprocess.run([md5sum_cmd], shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
            # Check the sums for paranoia sake
            self.check_md5(md5sum_path)
            os.chdir(cwd)
        except:
            self.failed("Failed to generate initial md5")

    def check_md5(self, file):
        print("Checking md5sums ...")
        try:
            check_md5_cmd = f"md5sum -c {file}"
            subprocess.run([check_md5_cmd], shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
        except:
            self.failed("Failed to generate initial md5")

    def generate_iso(self):
        # Generate ISO image
        print("Creating ISO Image ...")
        try:
            geniso_cmd =('genisoimage -input-charset UTF-8 -r -J '
                        f'-o {self.iso_name} {self.sample_file}')
            subprocess.run([geniso_cmd], shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
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
                           f'-Z {optical_drive}={self.iso_name}')
        else:
            print(f"Invalid type specified {optical_type}")
            self.failed("Failed to burn ISO image")
        try:
            subprocess.run([burn_iso_cmd], shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
        except:
            self.failed("Failed to burn ISO image")

    def check_disk(self):
        timeout = 300
        sleep_count = 0
        interval = 3

        # Give the tester up to 5 minutes to reload the newly created CD/DVD
        print("Waiting up to 5 minutes for drive to be mounted ...")

        while True:
            time.sleep(interval)
            sleep_count = sleep_count + interval
            
            mnt_cmd = subprocess.run(["mount", optical_drive],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            
            if 'already mounted' in mnt_cmd.stdout:
                print("Drive appears to be mounted now")
                break
            
            # If they exceed the timeout limit, make a best effort to load the 
            # tray in the next steps
            if sleep_count >= timeout:
                print("WARNING: TIMEOUT Exceeded and no mount detected!")
                break

        print("Deleting original data files ...")
        shutil.rmtree(self.sample_file)

        check_mnt_cmd = subprocess.check_output(['mount']).decode('utf-8')
        check_mnt_cmd = check_mnt_cmd.strip.split('\n')

        if any(optical_drive in line for line in check_mnt_cmd):
            for line in check_mnt_cmd:
                if optical_drive in line:
                    self.mount_pt = line.split()[2]
                    print(f"Disk is mounted to {self.mount_pt}")
        else:
            print(f"Attempting best effort to mount {optical_drive} on my own")
            self.mount_pt = os.path.join(self.tmp_dir, "/mnt")
            print("Creating temp mount point: $MOUNT_PT ...")
            os.mkdir(self.mount_pt)
            print("Mounting disk to mount point ...")

            mnt_cmd = subprocess.run(["mount", optical_drive, self.mount_pt],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            if mnt_cmd.returncode != 0:
                print(f"ERROR: Unable to re-mount {optical_drive}!")
                self.failed("Failed to verify files on optical disk")
        print("Copying files from ISO ...")
        try:
            source = self.mount_pt
            destination = self.tmp_dir
            shutil.copytree(source, destination)
            self.check_md5(self.md5sum_file)
        except:
            self.failed("Failed to verify files on optical disk")
                 
    def cleanup(self):
        print ("Moving back to original location")
        try:
            os.chdir(self.start_dir)
            cwd = os.getcwd()
            print(f"Now residing in {cwd}")
        except:
            self.failed("Failed to clean up")
            
        print("Cleaning up ...")
        try:
            subprocess.run(["umount", self.mount_pt],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
            shutil.rmtree(self.tmp_dir)
            print("Ejecting spent media ...")
            subprocess.run(["eject", optical_drive],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True)
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
    test.create_working_dirs()
    test.get_sample_data()
    test.generate_md5()
    test.generate_iso()
    test.burn_iso()
    test.check_disk()
    test.cleanup()
    sys.exit(0)