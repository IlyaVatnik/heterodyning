# -*- coding: utf-8 -*-
"""
oscilloscope binary parser, currently supports only single segmented traces
"""

def scope_bin_parser(fname):
    """
    scope parsing object, currently supports only single segmented traces
    currently no buffer available
    """
    with open(fname, mode='rb') as file:
        
        from numpy import dtype, fromfile
        
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
        file_dict= {}
        f_header = fromfile(file, dtype=file_header_dtype, count=1)
        file_dict['f_header']={}
        for key in f_header.dtype.names:
            file_dict['f_header'][key]=f_header[key][0]
        for n in range(f_header['num_waveforms'][0]):
            wf_header = fromfile(file, dtype=waveform_header_dtype, count=1)
            channel_string = bytes(wf_header['waveform_string'][0]).decode('utf-8').replace(' ', '_')
            file_dict[channel_string] = {}
            wf_dict=file_dict[channel_string]
            for key in wf_header.dtype.names:
                wf_dict[key]=wf_header[key][0]
            bf_header = fromfile(file, dtype=buffer_header_dtype, count=1)
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
            next_pos=file.tell()+bf_size
            wf_dict['data']=fromfile(file, dtype=dtype(f_str), count=num_points, offset=file.tell())
            file.seek(next_pos)
        return file_dict
    
  
        

        