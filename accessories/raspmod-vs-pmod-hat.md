# Raspmod and the Digilent Pmod HAT Adapter

Two boards put Digilent-style Pmod ports on a Raspberry Pi, and they do it in
opposite ways. The [Digilent Pmod HAT Adapter](output/pmod-hat.pdf)
(`ACC-PMOD-HAT`) is a HAT: it sits on the Pi's 40-pin header, and its three
hosts take whatever Pmod peripheral you plug into them. Pat
Deegan's [Raspmod](output/raspmod.pdf) (`ACC-RASPMOD`, "TT Demoboard To
Raspi") is a frontplate for a Tiny Tapeout demoboard: it plugs into the
demoboard's three Pmod hosts, passes them through to three hosts of its own,
and hands every signal to the Pi over a ribbon cable. One makes the Pi a Pmod
host; the other makes the Pi the thing on the far end of a Tiny Tapeout
chip's ports.

<table>
<tr>
<td width="50%" valign="top" align="center">
<a href="output/pmod-hat.pdf"><img src="output/previews/pmod-hat.png" width="270" alt="ACC-PMOD-HAT Digilent Pmod HAT Adapter"></a><br>
<b>ACC-PMOD-HAT</b> Digilent Pmod HAT Adapter
</td>
<td width="50%" valign="top" align="center">
<a href="output/raspmod.pdf"><img src="output/previews/raspmod.png" width="270" alt="ACC-RASPMOD Raspmod"></a><br>
<b>ACC-RASPMOD</b> Raspmod
</td>
</tr>
</table>

The tables on this page are written by `compare.py` from the same data the
two sheets are drawn from, `parts.py` and `raspmod.py`, so they cannot
disagree with the drawings. The Digilent figures are the ones the adapter's
own sheet carries: the HAT outline and holes from the Raspberry Pi HAT
specification, the host positions measured from Digilent's product photo to
about +/-0.75 mm, and the pin map transcribed from Digilent's reference
manual. The Raspmod figures are
read from its KiCad board file, pin map included.

## Mechanics

<!-- mechanics:begin -->

|  | Digilent Pmod HAT Adapter | Raspmod |
|---|---|---|
| Drawing | ACC-PMOD-HAT | ACC-RASPMOD |
| Outline | 65.0 x 56.5 mm, R3 corners | 72.3 x 31.3 mm, R2 corners |
| Thickness | not stated | 1.6 mm |
| Mounting holes | 4 x 2.75 mm, the HAT pattern | none |
| Pmod hosts | 3, right-angle, on two edges | 3, vertical, on the front face |
| Host pin-field centres (x, y) | JA (9.40, 39.29); JB (9.40, 16.43); JC (27.60, 9.40) | P1 (17.74, 14.29); P2 (40.60, 14.29); P3 (63.46, 14.29) |
| Host pitch | JA to JB 22.86 mm | 22.86 mm, both gaps |
| Plugs into | the Pi's 40-pin header, from above | the demoboard's 3 hosts: 3 underside plugs at (17.79, 4.13), (40.65, 4.13), (63.51, 4.13) |
| Pi connection | direct, as a HAT | 2x20 box header J1, ribbon cable |
| Position on the assembly | flat on top of the Pi, on M2.5 standoffs | on edge in front of the demoboard, component side forward |
<!-- mechanics:end -->

Coordinates are each board's own drawing frame: origin at the lower-left
corner, X right, Y up, viewed from the component side.

**The Pmod HAT Adapter** is the shape the HAT specification dictates,
65 x 56.5 mm with four M2.5 holes, and it mounts the only way a HAT can: on
the Pi's GPIO header, held off the Pi by standoffs through those holes. Its
hosts are right-angle sockets on the board edges, two on the left and one on
the bottom, so a Pmod plugged in lies flat and sticks out sideways from the
Pi, and the bottom host JC overhangs the Pi's HDMI and power connectors,
which is why Digilent's manual insists on the two standoffs opposite the
header. The Raspberry Pi sheets `RPI-3B`, `RPI-4B` and `RPI-5` draw it in
phantom on each Pi so those host positions can be read off directly.

**The Raspmod** has no mounting holes at all. Its three plugs are 2x6 pin
headers on the underside, pointing out of the back of the board, on the
demoboard's 22.86 mm host pitch. The demoboard's hosts are right-angle
sockets facing the front edge, so a board whose plugs go into them stands on
edge in front of the demoboard, component side facing forward, and that is
how the Raspmod is used: as a frontplate, 72.3 mm wide and 31.3 mm tall,
carried entirely by the six plug-and-socket engagements. Its own hosts are
vertical sockets on the front face, so an external Pmod plugs in from the
front, pointing forward, where it would have plugged into the demoboard. The
ribbon header is a 2x20 box along the top edge, pins forward, and the ribbon
leaves from the front too.

Which host each plug lands in is fixed by the pitch and by the clock/reset
pins: the Raspmod's port P1 meets the demoboard's INPUT host, P2 BIDIR and
P3 OUTPUT. Along the demoboard's front edge that puts the Raspmod here on
each three-host revision:

<!-- demoboards:begin -->

| Demoboard | Board width mm | Raspmod left edge at x | Raspmod right edge at x | Within the board's width |
|---|---|---|---|---|
| DB 4+ v1.2.1, DB 4+ v1.2.2, DB 4+ v1.2.2c | 104.5 | 9.90 | 82.20 | yes |
| DB 06+ v2.0.1, DB 06+ v2.1.0, DB 06+ v2.1.2 | 99.5 | 10.21 | 82.52 | yes |
| DB ETR v3.2, DB ETR v3.3 | 85.0 | 1.56 | 73.86 | yes |
<!-- demoboards:end -->

The mpw-mb1 board of TT01 to TT03 has two hosts and is not a fit: P2 and P3
would land on them, P1 would hang in the air to the left, and that board has
no clock/reset header at the front edge for J9 to meet.

The one thing the Pmod ports do not carry is the project clock and reset.
The Raspmod takes them from a 2-pin header on its underside, J9, which falls
on pins 2 and 3 of the demoboard's clock/reset SIL header (J17 on rev 2.1.2,
J9 on rev 3.3) to within 0.04 mm on both revisions. The SIL header is not
fitted on the demoboard as sold; Pat's README says a 2-pin header has to be
added there. `compare.py` re-measures that residual from the board files
whenever they are checked out under `tmp/pcb`.

How far in front of the demoboard's front edge the Raspmod's two faces sit
depends on the plug's pin length and the socket's depth, which the footprints
give as 6 mm and 8.51 mm but the board files do not pin down. It is on the
TODO list as a measurement to take.

## Pin maps

Both adapters put a Pmod pin on a Raspberry Pi GPIO, and there the
resemblance ends.

**Digilent** assigns each host a Pmod interface type and wires the Pi's
hardware bus for it: JA and JB carry SPI0 on pins 1 to 4, with JA1 as CE0 and
JB1 as CE1 and the MOSI, MISO and SCLK lines shared between them; JB's bottom
row carries I2C1 on pins 9 and 10, with pull-ups behind jumpers JP1 and JP2;
JC carries UART0 on pins 1 to 4. Five GPIOs, 22 to 25 and 27, are left free
for another HAT, and the ID EEPROM pins are the HAT's EEPROM. That is a
general-purpose Pmod host.

**The Raspmod** assigns nothing by interface type. Port P1 is the demoboard's
INPUT host, so its eight I/O pins are `ui_in[0..7]`; P2 is BIDIR, `uio[0..7]`;
P3 is OUTPUT, `uo_out[0..7]`; and the GPIO behind each was chosen to get all
24 lines, the clock, the reset, a button and a spare onto one 40-way cable.
All 26 of the Pi's general-purpose GPIOs, 2 to 27, are used, and so is the
ID EEPROM pair, GPIO0 and GPIO1, which carry the user switch and the project
clock. That is allowed, because it is not a HAT, but it means no HAT can
share the header. The Pi's 5 V pins are not connected; the board runs on the
Pi's 3V3, and jumper J11 puts that 3V3 onto the Pmod VCC rail, which is how
the demoboard is powered from the Pi. SPI0 does end up on P2, and UART0 and
I2C1 on P3, but scattered: of the four SPI0 lines only MOSI sits where a Pmod
SPI peripheral looks for it, and of the UART pair only RXD. A Pmod plugged
into a Raspmod host is driven pin by pin, not by a hardware bus.

### The Raspberry Pi header

Pin names are the ones KiCad's Raspberry Pi symbol gives the header, which
is what the Raspmod's schematic uses; an active-low signal written `~{CE0}`
there is `nCE0` here.

<!-- pi-header:begin -->

| Pi pin | Pi name | Pmod HAT Adapter | Raspmod |
|---|---|---|---|
| 1 | 3V3 | 3V3 rail | 3V3 from the Pi; J11 jumpers it to the Pmod VCC rail |
| 2 | 5V | 5 V in or out | not connected |
| 3 | SDA_I2C1/GPIO02 | JB10 | P3 pin 1, uo_out[0] |
| 4 | 5V | 5 V in or out | not connected |
| 5 | SCL_I2C1/GPIO03 | JB9 | P3 pin 7, uo_out[4] |
| 6 | GND | GND | GND |
| 7 | GPCLK0/GPIO04 | JC7 | P3 pin 2, uo_out[1] |
| 8 | GPIO14/UART_TXD | JC2 | P3 pin 8, uo_out[5] |
| 9 | GND | GND | GND |
| 10 | GPIO15/UART_RXD | JC3 | P3 pin 3, uo_out[2] |
| 11 | GPIO17/SPI1_nCE1 | JC4 | P3 pin 9, uo_out[6] |
| 12 | GPIO18/SPI1_nCE0/PCM_CLK/PWM0 | JA10 | P3 pin 4, uo_out[3] |
| 13 | GPIO27/SDIO_DAT3 | free | P3 pin 10, uo_out[7] |
| 14 | GND | GND | GND |
| 15 | GPIO22/SDIO_CLK | free | P2 pin 1, uio[0] |
| 16 | GPIO23/SDIO_CMD | free | P2 pin 7, uio[4] |
| 17 | 3V3 | 3V3 rail | 3V3 from the Pi; J11 jumpers it to the Pmod VCC rail |
| 18 | GPIO24/SDIO_DAT0 | free | P2 pin 8, uio[5] |
| 19 | MOSI_SPI0/GPIO10 | JA2, JB2 | P2 pin 2, uio[1] |
| 20 | GND | GND | GND |
| 21 | MISO_SPI0/GPIO09 | JA3, JB3 | P2 pin 9, uio[6] |
| 22 | GPIO25/SDIO_DAT1 | free | P2 pin 3, uio[2] |
| 23 | SCLK_SPI0/GPIO11 | JA4, JB4 | P2 pin 10, uio[7] |
| 24 | nCE0_SPI0/GPIO08 | JA1 | P2 pin 4, uio[3] |
| 25 | GND | GND | GND |
| 26 | nCE1_SPI0/GPIO07 | JB1 | nRST, the demoboard's project reset, via J8/J9 |
| 27 | ID_SD_I2C0/GPIO00 | ID EEPROM | USR_SW, push button SW1, also on J10 |
| 28 | ID_SC_I2C0/GPIO01 | ID EEPROM | CLK, the demoboard's project clock, via J8/J9 |
| 29 | GPCLK1/GPIO05 | JC9 | P1 pin 7, ui_in[4] |
| 30 | GND | GND | GND |
| 31 | GPCLK2/GPIO06 | JC10 | P1 pin 8, ui_in[5] |
| 32 | GPIO12/PWM0 | JC8 | P1 pin 1, ui_in[0] |
| 33 | GPIO13/PWM1 | JB8 | P1 pin 2, ui_in[1] |
| 34 | GND | GND | GND |
| 35 | GPIO19/SPI1_MISO/PCM_FS | JA7 | P1 pin 3, ui_in[2] |
| 36 | GPIO16/SPI1_nCE2 | JC1 | P1 pin 9, ui_in[6] |
| 37 | GPIO26/SDIO_DAT2 | JB7 | P1 pin 4, ui_in[3] |
| 38 | GPIO20/SPI1_MOSI/PCM_DIN/PWM1 | JA9 | P1 pin 10, ui_in[7] |
| 39 | GND | GND | GND |
| 40 | GPIO21/SPI1_SCLK/PCM_DOUT | JA8 | USR_IO, spare, on J10 |
<!-- pi-header:end -->

### Port by port

Pmod pins 5 and 11 are ground and 6 and 12 are VCC on every host of both
boards. On the Pmod HAT Adapter, VCC is the adapter's 3V3 rail; on the
Raspmod it is the `+3V3` net, which J11 connects to the Pi's 3V3.

<!-- ports:begin -->

**Digilent Pmod HAT Adapter**

| Pmod pin | JA | JB | JC |
|---|---|---|---|
| 1 | SPI0_CE0/GPIO08 (pin 24) | SPI0_CE1/GPIO07 (pin 26) | CTS0/GPIO16 (pin 36) |
| 2 | SPI0_MOSI/GPIO10 (pin 19) | SPI0_MOSI/GPIO10 (pin 19) | TXD0/GPIO14 (pin 8) |
| 3 | SPI0_MISO/GPIO09 (pin 21) | SPI0_MISO/GPIO09 (pin 21) | RXD0/GPIO15 (pin 10) |
| 4 | SPI0_CLK/GPIO11 (pin 23) | SPI0_CLK/GPIO11 (pin 23) | RTS0/GPIO17 (pin 11) |
| 5 | GND | GND | GND |
| 6 | 3V3 | 3V3 | 3V3 |
| 7 | PCM_FS/GPIO19/PWM1 (pin 35) | GPIO26 (pin 37) | GPCLK0/GPIO04 (pin 7) |
| 8 | PCM_DOUT/GPIO21/GPCLK1 (pin 40) | PWM1/GPIO13 (pin 33) | PWM0/GPIO12 (pin 32) |
| 9 | PCM_DIN/GPIO20/GPCLK0 (pin 38) | SCL1/GPIO03 (pin 5) | GPCLK1/GPIO05 (pin 29) |
| 10 | PCM_CLK/GPIO18/PWM0 (pin 12) | SDA1/GPIO02 (pin 3) | GPCLK2/GPIO06 (pin 31) |
| 11 | GND | GND | GND |
| 12 | 3V3 | 3V3 | 3V3 |

**Raspmod**

| Pmod pin | P1 = INPUT host | P2 = BIDIR host | P3 = OUTPUT host |
|---|---|---|---|
| 1 | GPIO12/PWM0 (pin 32), ui_in[0] | GPIO22/SDIO_CLK (pin 15), uio[0] | SDA_I2C1/GPIO02 (pin 3), uo_out[0] |
| 2 | GPIO13/PWM1 (pin 33), ui_in[1] | MOSI_SPI0/GPIO10 (pin 19), uio[1] | GPCLK0/GPIO04 (pin 7), uo_out[1] |
| 3 | GPIO19/SPI1_MISO/PCM_FS (pin 35), ui_in[2] | GPIO25/SDIO_DAT1 (pin 22), uio[2] | GPIO15/UART_RXD (pin 10), uo_out[2] |
| 4 | GPIO26/SDIO_DAT2 (pin 37), ui_in[3] | nCE0_SPI0/GPIO08 (pin 24), uio[3] | GPIO18/SPI1_nCE0/PCM_CLK/PWM0 (pin 12), uo_out[3] |
| 5 | GND | GND | GND |
| 6 | 3V3 (Pmod VCC rail) | 3V3 (Pmod VCC rail) | 3V3 (Pmod VCC rail) |
| 7 | GPCLK1/GPIO05 (pin 29), ui_in[4] | GPIO23/SDIO_CMD (pin 16), uio[4] | SCL_I2C1/GPIO03 (pin 5), uo_out[4] |
| 8 | GPCLK2/GPIO06 (pin 31), ui_in[5] | GPIO24/SDIO_DAT0 (pin 18), uio[5] | GPIO14/UART_TXD (pin 8), uo_out[5] |
| 9 | GPIO16/SPI1_nCE2 (pin 36), ui_in[6] | MISO_SPI0/GPIO09 (pin 21), uio[6] | GPIO17/SPI1_nCE1 (pin 11), uo_out[6] |
| 10 | GPIO20/SPI1_MOSI/PCM_DIN/PWM1 (pin 38), ui_in[7] | SCLK_SPI0/GPIO11 (pin 23), uio[7] | GPIO27/SDIO_DAT3 (pin 13), uo_out[7] |
| 11 | GND | GND | GND |
| 12 | 3V3 (Pmod VCC rail) | 3V3 (Pmod VCC rail) | 3V3 (Pmod VCC rail) |
<!-- ports:end -->

## Sources

- Digilent, *Pmod HAT Adapter Reference Manual*, Appendix: Pinout Tables, and
  the statement that the manual applies to Revision B:
  <https://digilent.com/reference/add-ons/pmod-hat/reference-manual>. Its
  mechanical figures are those of drawing `ACC-PMOD-HAT`,
  whose sources are on the sheet.
- Pat Deegan, *TT Demoboard To Raspi* rev 1.0, `TTDB_2_Raspi.kicad_pcb` at
  commit `2c2e3db`, and the README:
  <https://github.com/psychogenic/tinytapeout-demoboard-to-raspi>.
- Tiny Tapeout, `tinytapeout-demo.kicad_pcb` rev 2.1.2 and rev 3.3, for the
  host nets and the clock/reset SIL header:
  <https://github.com/TinyTapeout/tt-demo-pcb>.
