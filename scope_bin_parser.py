# -*- coding: utf-8 -*-

def scope_bin_parser(f_name):
    """
    scope parsing object, currently supports only single segmented traces
    currently no buffer available
    """
    f=open(f_name,'rb')
    import numpy as np
    
    file_header_dtype = np.dtype([('file_cookie', 'S2'),
                                  ('file_version', 'S2'),
                                  ('file_size', 'i4'),
                                  ('num_waveforms', 'i4')])
    waveform_header_dtype = np.dtype([('header_size', 'i4'),
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
    buffer_header_dtype = np.dtype([('header_size', 'i4'),
                                    ('buffer_type', 'i2'),
                                    ('bytes_per_point', 'i2'),
                                    ('buffer_size', 'i4')])
    f_dict={}
    f_header = np.fromfile(f, dtype=file_header_dtype, count=1)
    f_dict['f_header']={}
    for key in f_header.dtype.names:
        f_dict['f_header'][key]=f_header[key][0]
    
    for n in range(f_header['num_waveforms'][0]):
    
        wf_header = np.fromfile(f, dtype=waveform_header_dtype, count=1)
        channel_string = bytes(wf_header['waveform_string'][0]).decode('utf-8').replace(' ', '_')
        f_dict[channel_string] = {}
        wf_dict=f_dict[channel_string]
        for key in wf_header.dtype.names:
            wf_dict[key]=wf_header[key][0]
        
        bf_header = np.fromfile(f, dtype=buffer_header_dtype, count=1)
        wf_dict['bf_header']={}
        bf_dict=wf_dict['bf_header']
        for key in bf_header.dtype.names:
            bf_dict[key]=bf_header[key][0]
        
        bf_type = bf_header['buffer_type'][0]
        if bf_type in [1,2,3]:
            #Float
            f_str = 'f4'
        elif bf_type == 4:
            #Integer
            f_str = 'i4'
        else:
            #Boolean or other
            f_str = 'u1'
        
        num_points = wf_header['num_points'][0]
        bf_size=bf_header['buffer_size'][0]
    
        next_pos=f.tell()+bf_size
        #wf_dict['data']=np.memmap(f, dtype=np.dtype(f_str), shape=(num_points,), mode='r', offset=f.tell())
        wf_dict['data']=np.fromfile(f, dtype=np.dtype(f_str),count=num_points)
        f.seek(next_pos)
    f.close()
    return f_dict
    
  
        

        