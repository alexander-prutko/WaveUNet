import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class Sunet(nn.Module):
    def __init__(self,nefilters=24):
        super(Sunet, self).__init__()
        print('sunet')
        nlayers = 7 # 12
        self.num_layers = nlayers
        self.nefilters = nefilters
        filter_size = 3 # 15
        merge_filter_size = 3 # 5
        self.encoder = nn.ModuleList()
        self.decoder = nn.ModuleList()
        self.ebatch = nn.ModuleList()
        self.dbatch = nn.ModuleList()
        echannelin = [1] + [(i + 1) * nefilters for i in range(nlayers-1)]
        echannelout = [(i + 1) * nefilters for i in range(nlayers)]
        dchannelout = echannelout[::-1]
        dchannelin = [dchannelout[0]*2]+[(i) * nefilters + (i - 1) * nefilters for i in range(nlayers,1,-1)]
        for i in range(self.num_layers):
            self.encoder.append(nn.Conv2d(echannelin[i],echannelout[i],filter_size,padding=filter_size//2))
            self.decoder.append(nn.Conv2d(dchannelin[i],dchannelout[i],merge_filter_size,padding=merge_filter_size//2))
            self.ebatch.append(nn.BatchNorm2d(echannelout[i]))
            self.dbatch.append(nn.BatchNorm2d(dchannelout[i]))

        self.middle = nn.Sequential(
            nn.Conv2d(echannelout[-1],echannelout[-1],filter_size,padding=filter_size//2),
            nn.BatchNorm2d(echannelout[-1]),
            nn.LeakyReLU(0.1)
        )
        self.out = nn.Sequential(
            nn.Conv2d(nefilters + 1, 1, 1),
            nn.Tanh()
        )
    def forward(self,x):
        encoder = list()
        input = x
        for i in range(self.num_layers):
            x = self.encoder[i](x)
            x = self.ebatch[i](x)
            x = F.leaky_relu(x,0.1)
            encoder.append(x)
            print(x.size())
            print(encoder[-1].size())
            x = x[:,:,::2,::2]

        x = self.middle(x)

        print('=============')
        for i in range(self.num_layers):
            x = F.upsample(x,scale_factor=(2,2),mode='bilinear')
            print(x.size())
            print(encoder[self.num_layers - i - 1].size())
            x = torch.cat([x,encoder[self.num_layers - i - 1]],dim=1)
            x = self.decoder[i](x)
            x = self.dbatch[i](x)
            x = F.leaky_relu(x,0.1)
        x = torch.cat([x,input],dim=1)

        x = self.out(x)

        return x

