# ERROR CODES
NDI_INVALID = 0x01
NDI_BAD_CRC = 0x04
NDI_BAD_COMM = 0x06
NDI_NO_USER_PARAM = 0x34
NDI_PARAMETER_RANGE = 0x23

# BX REPLY OPTIONS
NDI_XFORMS_AND_STATUS = 0x0001      # transforms and status
NDI_ADDITIONAL_INFO = 0x0002        # additional tool transform info
NDI_SINGLE_STRAY = 0x0004           # stray active marker reporting
NDI_FRAME_NUMBER = 0x0008           # frame number for each tool
NDI_PASSIVE = 0x8000                # report passive tool information
NDI_PASSIVE_EXTRA = 0x2000          # add 6 extra passive tools
NDI_PASSIVE_STRAY = 0x1000          # stray passive marker reporting 

# PHRQ REPLY OPTIONS
NDI_ALL_HANDLES = 0x00              # return all handles
NDI_STALE_HANDLES = 0x01            # only handles waiting to be freed
NDI_UNINITIALIZED_HANDLES = 0x02    # handles needing initialization
NDI_UNENABLED_HANDLES = 0x03        # handles needing enabling
NDI_ENABLED_HANDLES = 0x04          # handles that are enabled

VER_STR_CUSTOM = \
"""Polaris Vicra Control Firmware
NDI S/N: P6-00000
Characterization Date: 06/05/24
Freeze Tag: Polaris Vicra Rev 007.000
Freeze Date: 01/04/10
(C) Northern Digital Inc.
"""

APIREV_STR = "G.001.005"

GET_ATTRS = \
"""Cmd.VSnap.Illuminated Frame=0
Cmd.VSnap.Background Frame=0
Cmd.VSnap.Manual Shutter=300
Cmd.VSnap.Frame Types=0
Cmd.VGet.Threshold.Shutter Time=0
Cmd.VGet.Threshold.Trigger=4.98047
Cmd.VGet.Threshold.Background=3.125
Cmd.VGet.Sensor.Color Depth=12
Cmd.VGet.Sensor.Width=768
Cmd.VGet.Sensor.Height=243
Cmd.VGet.Start X=0
Cmd.VGet.End X=767
Cmd.VGet.Color Depth=16
Cmd.VGet.Stride=1
Cmd.VGet.Sample Option=0
Cmd.VGet.Compression=0
Param.User.String0=
Param.User.String1=
Param.User.String2=
Param.User.String3=
Param.User.String4=
Param.Firmware.Current Version=007.000.011
Param.Tracking.Available Volumes=Vicra
Param.Tracking.Selected Volume=0
Param.Tracking.Sensitivity=4
Param.Tracking.Illuminator Rate=0
Param.Default Wavelength.Return Warning=1
Param.Bump Detector.Bump Detection=1
Param.Bump Detector.Clear=0
Param.Bump Detector.Bumped=0
Param.System Beeper=1
Param.Watch Dog Timer=0
Param.Simulated Alerts=0
Param.Host Connection=0
Info.Timeout.INIT=4
Info.Timeout.COMM=2
Info.Timeout.VER=2
Info.Timeout.PHRQ=2
Info.Timeout.PINIT=6
Info.Timeout.PENA=2
Info.Timeout.PDIS=2
Info.Timeout.PHF=2
Info.Timeout.PVWR=2
Info.Timeout.PHSR=2
Info.Timeout.PHINF=2
Info.Timeout.PFSEL=2
Info.Timeout.TSTART=6
Info.Timeout.TSTOP=2
Info.Timeout.TX=4
Info.Timeout.BX=4
Info.Timeout.VSNAP=2
Info.Timeout.VGET=2
Info.Timeout.DSTART=6
Info.Timeout.DSTOP=2
Info.Timeout.IRED=2
Info.Timeout.3D=4
Info.Timeout.PSTART=6
Info.Timeout.PSTOP=2
Info.Timeout.GP=4
Info.Timeout.GETLOG=4
Info.Timeout.SYSLOG=8
Info.Timeout.SFLIST=2
Info.Timeout.VSEL=2
Info.Timeout.SSTAT=2
Info.Timeout.IRATE=2
Info.Timeout.BEEP=2
Info.Timeout.HCWDOG=2
Info.Timeout.SENSEL=2
Info.Timeout.ECHO=2
Info.Timeout.SET=8
Info.Timeout.GET=8
Info.Timeout.GETINFO=15
Info.Timeout.DFLT=2
Info.Timeout.SAVE=8
Info.Timeout.RESET=15
Info.Timeout.APIREV=2
Info.Timeout.GETIO=2
Info.Timeout.SETIO=2
Info.Timeout.LED=2
Info.Timeout.PPRD=4
Info.Timeout.PPWR=4
Info.Timeout.PSEL=2
Info.Timeout.PSRCH=4
Info.Timeout.PURD=4
Info.Timeout.PUWR=4
Info.Timeout.TCTST=2
Info.Timeout.TTCFG=2
Info.Timeout.PSOUT=2
Info.Status.System Mode=Initialized
Info.Status.Alerts=0
Info.Status.New Alerts=0
Info.Status.Alerts Overflow=0
Info.Status.Bump Detected=0
Info.Status.New Log Entry=0
Features.Keys.Installed Keys.0=
Features.Keys.Disabled Keys=
Features.Tools.Enabled Tools=15
Features.Tools.Active Ports=0
Features.Tools.Passive Ports=6
Features.Tools.Wireless Ports=1
Features.Firmware.Version=007.000.011
Features.Firmware.Major Version=007
Features.Firmware.Minor Version=000
Features.Firmware.Build Number=011
Features.Firmware.Available Versions=1: 007.000.011
Features.Firmware.Maximum Versions=1
Features.Firmware.Configuration Check=0
Features.Firmware.Package Number=014.002
Features.Firmware.Combined Firmware Revision=014
Features.Firmware.Available Combined Firmware Revisions=014
Features.Firmware.Safeloader Version=007.000.011
Features.Hardware.Serial Number=P6-00470
Features.Hardware.OEM Number= 
Features.Hardware.Model=Polaris Vicra
Config.Multi Firmware.Load Combined Firmware Revision=0
Config.Multi Firmware.Update Combined Firmware Revision=0
Config.Multi Firmware.Available Combined Firmware Revisions=014
Config.Password=
Config.Combined Firmware Revision=014
Config.Ext Device Syncing=0
Device.Type.0=PS
Device.Instance.0=0
"""