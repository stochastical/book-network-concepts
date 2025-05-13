for i in {0..9}; do
    txt_file="tcp_data/tcp_addrs_$i.txt"
    dat_file="tcp_data/tcp_data_$i.dat"
    python3 validate_tcp_packet.py "$txt_file" "$dat_file" 
done
