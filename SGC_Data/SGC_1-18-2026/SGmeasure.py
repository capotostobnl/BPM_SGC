"""Data Collection script for Static Gain Calibration
5/20/2025"""

from cothread.catools import caget, caput
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
import os
from math import sqrt

#  create the subdirectories if necessary:
if not os.path.exists("Old_SG_Tables"):
    os.makedirs("Old_SG_Tables")
if not os.path.exists("New_SG_Tables"):
    os.makedirs("New_SG_Tables")
if not os.path.exists("Images"):
    os.makedirs("Images")
if not os.path.exists("Data"):
    os.makedirs("Data")

#  cell[01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]
# Nbpm = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 9, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0,0]
Nbpm = [6, 8, 8, 10, 9, 6, 10, 8, 6, 8, 8, 10, 6, 6, 6, 8, 9, 8, 10, 8, 8, 6,
        9, 6, 6, 6, 8, 8, 6, 10]
#  The mask below allows the user to mask off any BPM from this script.  For
#  example, for Cell 1 if all 6 BPMs are to be scanned the mask would be 0x3F
#  but if you want to disable BPM3 then the
#  mask would be 0x3B (b111011)

#  cell[  1      2      3      4      5      6      7      8      9     10     11     12     13     14     15  ]  # noqa: E501
Mask = [0x03F, 0x0FF, 0x0FF, 0x3FF, 0x1FF, 0x03F, 0x3FF, 0x0FF, 0x03F, 0x0FF, 0x0FF, 0x3FF, 0x03F, 0x03F, 0x03F,  # noqa: E501
        0x0FF, 0x1FF, 0x0FF, 0x3FF, 0x0FF, 0x0FF, 0x03F, 0x1FF, 0x03F, 0x03F, 0x03F, 0x0FF, 0x0FF, 0x03F, 0x3FF]  # noqa: E501
#  cell[  16     17     18     19     20     21     22     23     24     25     26     27     28     29     30 ]  # noqa: E501

PUEpv = []
RGAINpv = []
Kpv = []
GAsp = []
GBsp = []
GCsp = []
GDsp = []
RFsp = []
BPMname = []


# Here, arrays of all the required PVs are declared:
for c in range(0, 30):
    M = Mask[c]
    for b in range(0, Nbpm[c]):
        if ((M & pow(2, b)) > 0):
            if (c + 1 < 10):
                BPMname.append("SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}")
                Apv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:ASA-I"
                Bpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:BSA-I"
                Cpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:CSA-I"
                Dpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:DSA-I"
                GArbpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc0-I"
                GBrbpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc1-I"
                GCrbpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc2-I"
                GDrbpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc3-I"
                KXpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Kx-SP"
                KYpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ky-SP"
                GAsppv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc0-SP"
                GBsppv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc1-SP"
                GCsppv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc2-SP"
                GDsppv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc3-SP"
                RFpv = "SR:C0"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:RfAtte-SP"
            else:
                BPMname.append("SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}")
                Apv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:ASA-I"
                Bpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:BSA-I"
                Cpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:CSA-I"
                Dpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ampl:DSA-I"
                GArbpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc0-I"
                GBrbpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc1-I"
                GCrbpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc2-I"
                GDrbpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc3-I"
                KXpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Kx-SP"
                KYpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Ky-SP"
                GAsppv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc0-SP"
                GBsppv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc1-SP"
                GCsppv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc2-SP"
                GDsppv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:Adc3-SP"
                RFpv = "SR:C"+str(c+1)+"-BI{BPM:"+str(b+1)+"}Gain:RfAtte-SP"

            PUEpv.append(Apv)
            PUEpv.append(Bpv)
            PUEpv.append(Cpv)
            PUEpv.append(Dpv)
            RGAINpv.append(GArbpv)
            RGAINpv.append(GBrbpv)
            RGAINpv.append(GCrbpv)
            RGAINpv.append(GDrbpv)
            Kpv.append(KXpv)
            Kpv.append(KYpv)
            GAsp.append(GAsppv)
            GBsp.append(GBsppv)
            GCsp.append(GCsppv)
            GDsp.append(GDsppv)
            RFsp.append(RFpv)

K = np.array(caget(Kpv))
K = np.multiply(K, 1000.0)  # Convert mm to um
N = int(len(K)/2)
K = K.reshape(N, 2)

X1 = np.zeros((N, 32))
Y1 = np.zeros((N, 32))
X2 = np.zeros((N, 32))
Y2 = np.zeros((N, 32))
X3 = np.zeros((N, 32))
Y3 = np.zeros((N, 32))
X4 = np.zeros((N, 32))
Y4 = np.zeros((N, 32))
A = np.zeros((N, 32))
B = np.zeros((N, 32))
C = np.zeros((N, 32))
D = np.zeros((N, 32))
SG0 = np.zeros((N, 32, 5))
SG1 = np.zeros((N, 32, 5))

for i in range(0, 32):
    print(i)

    caput(RFsp, 0, repeat_value=True, wait=True, timeout=10)
    caput(GAsp, 32767, repeat_value=True, wait=True, timeout=10)
    caput(GBsp, 32767, repeat_value=True, wait=True, timeout=10)
    caput(GCsp, 32767, repeat_value=True, wait=True, timeout=10)
    caput(GDsp, 32767, repeat_value=True, wait=True, timeout=10)
    sleep(9)
    PU = np.array(caget(PUEpv))
    PU = PU.reshape(N, 4)
    A0 = []
    B0 = []
    C0 = []
    D0 = []
    for j in range(0, N):
        A0.append(PU[j][0])
        B0.append(PU[j][1])
        C0.append(PU[j][2])
        D0.append(PU[j][3])

#   print(i,A0,B0,C0,D0)

    caput(RFsp, i, repeat_value=True, wait=True, timeout=10)
    sleep(3)
    RG = np.array(caget(RGAINpv))
    RG = RG.reshape(N, 4)
#   print(RG)
    PU = np.array(caget(PUEpv))
    PU = PU.reshape(N, 4)
    A1 = []
    B1 = []
    C1 = []
    D1 = []
    for j in range(0, N):
        SG0[j][i][0] = i
        SG0[j][i][1] = RG[j][0]
        SG0[j][i][2] = RG[j][1]
        SG0[j][i][3] = RG[j][2]
        SG0[j][i][4] = RG[j][3]
        A1.append(PU[j][0])
        B1.append(PU[j][1])
        C1.append(PU[j][2])
        D1.append(PU[j][3])
        X4[j][i] = K[j][0]*(A1[j]+D1[j]-B1[j]-C1[j])/(A1[j]+B1[j]+C1[j]+D1[j])
        Y4[j][i] = K[j][1]*(A1[j]+B1[j]-C1[j]-D1[j])/(A1[j]+B1[j]+C1[j]+D1[j])
#      print(X4[j][i],Y4[j][i],"Original SG Table Position")
    caput(GAsp, 32767, repeat_value=True, wait=True, timeout=10)
    caput(GBsp, 32767, repeat_value=True, wait=True, timeout=10)
    caput(GCsp, 32767, repeat_value=True, wait=True, timeout=10)
    caput(GDsp, 32767, repeat_value=True, wait=True, timeout=10)
    sleep(9)
    PU = np.array(caget(PUEpv))
    PU = PU.reshape(N, 4)
    A1 = []
    B1 = []
    C1 = []
    D1 = []
    for j in range(0, N):
        A1.append(PU[j][0])
        B1.append(PU[j][1])
        C1.append(PU[j][2])
        D1.append(PU[j][3])

#   print(i,A1,B1,C1,D1)

    GAc = []
    GBc = []
    GCc = []
    GDc = []
    for j in range(0, N):
        A[j][i] = A1[j]
        B[j][i] = B1[j]
        C[j][i] = C1[j]
        D[j][i] = D1[j]

        dA = A1[j]/A0[j]
        dB = B1[j]/B0[j]
        dC = C1[j]/C0[j]
        dD = D1[j]/D0[j]
        dMin = min([dA, dB, dC, dD])

        dA = int(round(32767.0*dMin/dA, 0))
        dB = int(round(32767.0*dMin/dB, 0))
        dC = int(round(32767.0*dMin/dC, 0))
        dD = int(round(32767.0*dMin/dD, 0))
        row = [i, dA, dB, dC, dD]
        SG1[j][i] = row
        dMin = min(row)
#      print(row)
        GAc.append(round(dA/32767.0, 6))
        GBc.append(round(dB/32767.0, 6))
        GCc.append(round(dC/32767.0, 6))
        GDc.append(round(dD/32767.0, 6))

        X1[j][i] = K[j][0]*(A1[j]+D1[j]-B1[j]-C1[j])/(A1[j]+B1[j]+C1[j]+D1[j])
        Y1[j][i] = K[j][1]*(A1[j]+B1[j]-C1[j]-D1[j])/(A1[j]+B1[j]+C1[j]+D1[j])
#      print(X1[j][i],Y1[j][i])

        Sum = (dA*A[j][i]+dB*B[j][i]+dC*C[j][i]+dD*D[j][i])
        X2[j][i] = K[j][0]*(dA*A[j][i]-dB*B[j][i]-dC*C[j][i]+dD*D[j][i])/Sum
        Y2[j][i] = K[j][1]*(dA*A[j][i]+dB*B[j][i]-dC*C[j][i]-dD*D[j][i])/Sum
#      print(X2[j][i],Y2[j][i])

    caput(GAsp, GAc, repeat_value=False, wait=True)
    caput(GBsp, GBc, repeat_value=False, wait=True)
    caput(GCsp, GCc, repeat_value=False, wait=True)
    caput(GDsp, GDc, repeat_value=False, wait=True)
    sleep(9)

    PU = np.array(caget(PUEpv))
    PU = PU.reshape(N, 4)
    A1 = []
    B1 = []
    C1 = []
    D1 = []
    for j in range(0, N):
        A1.append(PU[j][0])
        B1.append(PU[j][1])
        C1.append(PU[j][2])
        D1.append(PU[j][3])
        X3[j][i] = K[j][0]*(A1[j]+D1[j]-B1[j]-C1[j])/(A1[j]+B1[j]+C1[j]+D1[j])
        Y3[j][i] = K[j][1]*(A1[j]+B1[j]-C1[j]-D1[j])/(A1[j]+B1[j]+C1[j]+D1[j])
#      print(X3[j][i],Y3[j][i])

RMSData = "Data/RmsData.txt"
frms = open(RMSData, "w")
for j in range(0, N):
    OldName = "Old_SG_Tables/"+BPMname[j]+"_OLD.txt"
    NewName = "New_SG_Tables/"+BPMname[j]+"_NEW.txt"
    Osg = open(OldName, 'w')
    Nsg = open(NewName, 'w')
    DataName = "Data/"+BPMname[j]+"_Data.txt"
    fxy = open(DataName, "w")
# Calculate the RMS values for all X and Y data arrays sqrt((X-Xavg)**2))
    RX1 = sqrt(sum(np.power(np.subtract(X1[j], np.mean(X1[j])), 2)))
    RX2 = sqrt(sum(np.power(np.subtract(X2[j], np.mean(X2[j])), 2)))
    RX3 = sqrt(sum(np.power(np.subtract(X3[j], np.mean(X3[j])), 2)))
    RX4 = sqrt(sum(np.power(np.subtract(X4[j], np.mean(X4[j])), 2)))
    RY1 = sqrt(sum(np.power(np.subtract(Y1[j], np.mean(Y1[j])), 2)))
    RY2 = sqrt(sum(np.power(np.subtract(Y2[j], np.mean(Y2[j])), 2)))
    RY3 = sqrt(sum(np.power(np.subtract(Y3[j], np.mean(Y3[j])), 2)))
    RY4 = sqrt(sum(np.power(np.subtract(Y4[j], np.mean(Y4[j])), 2)))
    frms.write("%8.3f,%8.3f,%8.3f,%8.3f,%8.3f,%8.3f,%8.3f,%8.3f,%s\n" %
               (RX1, RX2, RX3, RX4, RY1, RY2, RY3, RY4, BPMname[j]))
    for i in range(0, 32):
        fxy.write("%8.3f,%8.3f,%8.3f,%8.3f,%8.3f,%8.3f,%8.3f,%8.3f\n" %
                  (X1[j][i], X2[j][i], X3[j][i], X4[j][i], Y1[j][i], Y2[j][i],
                   Y3[j][i], Y4[j][i]))
        Odat = np.round(SG0[j][i], 0).astype(int)
        Ndat = np.round(SG1[j][i], 0).astype(int)
        if (i < 31):
            Osg.write("%d,%d,%d,%d,%d,\n" % (SG0[j][i][0], SG0[j][i][1],
                                             SG0[j][i][2], SG0[j][i][3],
                                             SG0[j][i][4]))
            Nsg.write("%d,%d,%d,%d,%d,\n" % (SG1[j][i][0], SG1[j][i][1],
                                             SG1[j][i][2], SG1[j][i][3],
                                             SG1[j][i][4]))
        else:
            Osg.write("%d,%d,%d,%d,%d#\n" % (SG0[j][i][0], SG0[j][i][1],
                                             SG0[j][i][2], SG0[j][i][3],
                                             SG0[j][i][4]))
            Nsg.write("%d,%d,%d,%d,%d#\n" % (SG1[j][i][0], SG1[j][i][1],
                                             SG1[j][i][2], SG1[j][i][3],
                                             SG1[j][i][4]))
    Osg.close()
    Nsg.close()
    fxy.close()

for j in range(0, N):
    f = plt.figure(figsize=(7, 9))
    plt.subplot(2, 1, 1)
    plt.plot(X1[j], "-o", label="Beam without Correction")
    plt.plot(X2[j], "-o", label="Correction Prediction")
    plt.plot(X3[j], "-o", label="Beam with Correction")
    plt.plot(X4[j], "-o", label="Beam with old SG Table")
    plt.xlabel("Attenuation (dB)")
    plt.ylabel("X Position (um)")
    plt.legend()
    plt.title(BPMname[j])
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(Y1[j], "-o", label="Beam without Correction")
    plt.plot(Y2[j], "-o", label="Correction Prediction")
    plt.plot(Y3[j], "-o", label="Beam with Correction")
    plt.plot(Y4[j], "-o", label="Beam with old SG Table")
    plt.grid(True)
    plt.xlabel("Attenuation (dB)")
    plt.ylabel("Y Position (um)")
    plt.legend()
    plt.savefig("Images/"+BPMname[j]+".png")

    plt.close(f)

# plt.show()

exit()
