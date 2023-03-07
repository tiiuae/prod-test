#!/bin/bash
##############################################################################################################
#
# This script is based on https://ssrc.atlassian.net/wiki/spaces/RIS/pages/662208772/Saluki+v1.1+wake-up+guide
# Prerequisites: 
#	* FPGA needs to be programmed with e.g. FlashPro Express (Windows).
#	* Microchip tools: LiberoSoc & SoftConsole 
#		https://ssrc.atlassian.net/wiki/spaces/DRON/pages/570655042/Saluki+Setup
#	* Microchip udev rules need to be set, otherwise commands need sudo and script does not work.
#	* For FlashPro5: 
#		https://onlinedocs.microchip.com/pr/GUID-FABC58FF-E2CC-4557-BA80-9C03AAFAA2D2-en-US-6/index.html?GUID-6F0EC6C9-241E-452C-#A25C-6A92F064CA91
#	* SSRC udevrules?
#	* Clone px4-firmware and prod-test form github.com/tiiuae
#	* install saluki-setup-tool .deb or form source: github.com/tiiuae
#	
# Sources:
# https://superuser.com/questions/375223/watch-the-output-of-a-command-until-a-particular-string-is-observed-and-then-e
#
#
#
##############################################################################################################

# Point environmental variable to PX4 FW file
#export SALUKI_FW="~/Saluki/ssrc_saluki-v2_default.px4"
	
echo -e "\nFlash bootloader"
echo "---------------------------------------------------------------------"
java -jar ${SC_INSTALL_DIR}/extras/mpfs/mpfsBootmodeProgrammer.jar --bootmode 1 --die MPFS250T ssrc_saluki-v2_bootloader.elf

echo -e "\nFind Saluki device name"
echo "---------------------------------------------------------------------"

# https://stackoverflow.com/questions/26188182/pause-the-bash-script-until-dmesg-w-outputs-anything


#for i in 1 2 3 4 5
#do
#   echo "Waiting for Saluki to mount..."
#   if []
#   sleep 1
#done
echo "Waiting for Saluki to mount..."
for i in 5 4 3 2 1
do
   printf "$i ";
   sleep 1
done
readarray lines <<< $(saluki-setup-tool list-saluki-devices)
sleep 1
read -a device <<< ${lines[4]}
#echo ${lines[4]}
echo $device

echo -e "\nPartition Saluki"
echo "---------------------------------------------------------------------"
sudo saluki-setup-tool create-partition $device sampleConfig.json  #TODO: Get rid of sudo. Udev rules SSRC??
ORANGE='\033[0;33m'
NC='\033[0m' # No Color
# These in case OpenOCD reboot is not used...
#printf "${ORANGE}*** Please manually power cycle Saluki, then press any key to continue! ***\n${NC}"
#read -p ""

echo -e "\nReset Saluki via OpenOCD"
echo "---------------------------------------------------------------------"
gnome-terminal -- sh -c '~/Microchip/SoftConsole-v2021.3-7.0.0.599/openocd/bin/openocd -c "set DEVICE MPFS" --file board/microsemi-riscv.cfg -c "bindto 0.0.0.0"'

sleep 1
echo "Resetting Polarfire..."
{ echo "reset halt"; sleep 1; echo "reset run"; sleep 1; echo "shutdown"; sleep 1; } | telnet 0.0.0.0 4444

sleep 1

echo -e "\nFlash PX4 firmware" #TODO: retry fw flash if verify error.
echo "---------------------------------------------------------------------"

python3 ~/px4-firmware/Tools/px_uploader.py --port /dev/ttyACM0 --baud-bootloader 2000000 ssrc_saluki-v2_default.px4


echo -e "\nRun AutomatedSalukiDiagnostic tool"
echo "---------------------------------------------------------------------"
python3 ~/prod-test/AutomatedSalukiDiagnostic_Linux.py

echo -e "If all tests passed, it is time to take her for a maiden flight... Good luck!"

