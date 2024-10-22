#!/bin/bash

pushd . >/dev/null
pushd `dirname $0` > /dev/null
export SCRIPTDIR=`pwd`
popd > /dev/null

rootapp=""

function edit_boot {
  if [ -e "/boot/armbianEnv.txt" ]; then
    echo "Backing up armbianEnv.txt"
    cp /boot/armbianEnv.txt /boot/armbianEnv.txt.bak
    grep -q -e "^overlays=.*spi-spidev" "/boot/armbianEnv.txt" || sed -i 's#overlays=\(.*\)#overlays=\1 spi-spidev#' "/boot/armbianEnv.txt"
    grep -q -e "^param_spidev_spi_bus=" "/boot/armbianEnv.txt" || echo "param_spidev_spi_bus=1" >> /boot/armbianEnv.txt
    grep -q -e "param_spidev_max_freq=" "/boot/armbianEnv.txt" || echo "param_spidev_max_freq=100000000" >> /boot/armbianEnv.txt
  fi
}

function main {
echo Creating /etc/udev/rules.d/50-spi.rules
echo 'SUBSYSTEM=="spidev", GROUP="spiuser", MODE="0660"' > /etc/udev/rules.d/50-spi.rules
groupadd spiuser
echo Creating /etc/udev/rules.d/50-i2c.rules
echo 'SUBSYSTEM=="i2c-dev", GROUP="i2cuser", MODE="0660"SUBSYSTEM=="i2c-dev", GROUP="i2cuser", MODE="0660"' > /etc/udev/rules.d/50-i2c.rules
groupadd i2cuser
echo Creating /etc/udev/rules.d/50-gpio.rules
echo "SUBSYSTEM==\"gpio*\", PROGRAM=\"/bin/sh -c '\\" > /etc/udev/rules.d/50-gpio.rules
echo '        chown -R root:gpiouser /sys/class/gpio && chmod -R 770 /sys/class/gpio;\' >> /etc/udev/rules.d/50-gpio.rules
echo '        chown -R root:gpiouser /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio;\' >> /etc/udev/rules.d/50-gpio.rules
echo '        chown -R root:gpiouser /sys$devpath && chmod -R 770 /sys$devpath\'  >> /etc/udev/rules.d/50-gpio.rules
echo "'\"" >> /etc/udev/rules.d/50-gpio.rules
groupadd gpiouser

echo ""
if [ ! -z $1 ]
then
adduser "$1" spiuser
adduser "$1" i2cuser
adduser "$1" gpiouser
echo "Added '$1' to spiuser-, i2cuser- and gpiouser-groups."
fi
echo -e "Please, reboot for the changes to take effect.\n"
read -n1 -p "Press any key to exit."
}

cd "$SCRIPTDIR"
if [ ! -z "$DISPLAY" ]
then
xrandr > /dev/null 2>/dev/null
if [ $? -eq 0 ]
then

which xterm >/dev/null 2>/dev/null
if [ $? -eq 0 ]
then
rootapp="xterm -e"
fi

which qterminal >/dev/null 2>/dev/null
if [ $? -eq 0 ]
then
rootapp="qterminal -e"
fi

fi
fi

if [ $EUID -eq 0 ]
then
edit_boot
main "$1"
exit 0
fi

cp $(basename $0) /tmp/enable-non-root-gpio.sh
$rootapp sudo /tmp/enable-non-root-gpio.sh "$(whoami)"
rm /tmp/enable-non-root-gpio.sh
exit 0
