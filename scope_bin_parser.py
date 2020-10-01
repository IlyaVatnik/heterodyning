# -*- coding: utf-8 -*-
"""
oscilloscope binary parser, currently supports only single segmented traces
"""

class scope_bin_parser:
    """
    scope parsing object, currently supports only single segmented traces
    currently no buffer available
    """
    def __init__(self, fname, buffered=False):
        
        from numpy import dtype, fromfile, memmap
        
        self.file=open(fname, mode='rb')
        
        file_header_dtype = dtype([('file_cookie', 'S2'),
                                      ('file_version', 'S2'),
                                      ('file_size', 'i4'),
                                      ('num_waveforms', 'i4')])

        waveform_header_dtype = dtype([('header_size', 'i4'),
                                          ('waveform_type', 'i4'),
                                          ('num_waveform_buffers', 'i4'),
                                          ('num_points', 'i4'),
                                          ('count', 'i4'),
                                          ('x_display_range', 'f4'),
                                          ('x_display_origin', 'f8'),
                                          ('x_increment', 'f8'),
                                          ('x_origin', 'f8'),
                                          ('x_units', 'i4'),
                                          ('y_units', 'i4'),
                                          ('date_string', 'S16'),
                                          ('time_string', 'S16'),
                                          ('frame_string', 'S24'),
                                          ('waveform_string', 'S16'),
                                          ('time_tag', 'f8'),
                                          ('segment_index', 'u4')])

        buffer_header_dtype = dtype([('header_size', 'i4'),
                                        ('buffer_type', 'i2'),
                                        ('bytes_per_point', 'i2'),
                                        ('buffer_size', 'i4')])

        self.dict = {}
        f_header = fromfile(self.file, dtype=file_header_dtype, count=1)
        self.dict['f_header']={}
        for key in f_header.dtype.names:
            self.dict['f_header'][key]=f_header[key][0]
        for n in range(f_header['num_waveforms'][0]):
            wf_header = fromfile(self.file, dtype=waveform_header_dtype, count=1)
            channel_string = bytes(wf_header['waveform_string'][0]).decode('utf-8').replace(' ', '_')
            self.dict[channel_string] = {}
            wf_dict=self.dict[channel_string]
            for key in wf_header.dtype.names:
                wf_dict[key]=wf_header[key][0]
            bf_header = fromfile(self.file, dtype=buffer_header_dtype, count=1)
            wf_dict['bf_header']={}
            bf_dict=wf_dict['bf_header']
            for key in bf_header.dtype.names:
                bf_dict[key]=bf_header[key][0]    
            bf_type = bf_header['buffer_type'][0]
            if bf_type in [1,2,3]:
                f_str = 'f4' #Float
            elif bf_type == 4:
                f_str = 'i4' #Integer
            else:
                f_str = 'u1' #Boolean or other
            num_points = wf_header['num_points'][0]
            bf_size=bf_header['buffer_size'][0]
            next_pos=self.file.tell()+bf_size
            if buffered:
                wf_dict['data']=memmap(self.file, dtype=dtype(f_str), shape=(num_points,), mode='r', offset=self.file.tell())
                self.is_buffered=True
            else:
                wf_dict['data']=fromfile(self.file, dtype=dtype(f_str), count=num_points, offset=self.file.tell())
                self.is_buffered=False
            self.file.seek(next_pos)
        if not buffered:
            self.file.close()

    def __del__(self):
        if self.is_buffered:
            for key in self.dict.keys():
                if 'Channel' in key:
                    del self.dict[key]['data']
            self.file.close()
        del self.dict
        

        