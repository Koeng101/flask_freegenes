import zipfile 
import requests
import wget
import subprocess
import os
import shutil
import pandas as pd
import os
import boto3

import time
from .models import Files

def sequence_link(run_name, pileups, reads, tmp_location='./.tmp'):
    # Combine file of csvs together
    big_seq = []
    for pileup in pileups:
        big_seq.append(pileup['full_search_sequence'])
    big_seq = ''.join(big_seq)

    # Init by removing
    try:
        shutil.rmtree(tmp_location)
    except OSError:
        print('Failed to delete tmp')
    else:
        print('Deleted tmp')

    # Add directory
    try:
        os.mkdir(tmp_location)
    except OSError:
        print('Failed to create tmp')
    else:
        print('Created tmp')

    # Run alignment and write combined pileup file
    pileup_loc = './.tmp/{}.pileup'.format(run_name)
    with open('./.tmp/tmp.fasta', 'w') as the_file:
        the_file.write('>tmp_fasta\n{}'.format(big_seq))
    command = 'bwa index ./.tmp/tmp.fasta && bwa mem ./.tmp/tmp.fasta {} | samtools view -bS - | samtools sort - | samtools mpileup -f ./.tmp/tmp.fasta - > {}'.format(' '.join(reads), pileup_loc)
    pileup_file = subprocess.check_output(command,shell=True)

    # Read pileup file into pandas
    combined_pileup = pd.read_table('{}'.format(pileup_loc), names = ["Sequence", "Position", "Reference Base", "Read Count", "Read Results", "Quality"])
    combined_pileup = combined_pileup.set_index('Position')

    # Create output directory for files
    output_directory = './outputs/{}'.format(run_name)
    os.makedirs(output_directory,exist_ok=True)

    # Make pileup files per gene

    for pileup in pileups:
        length = len(pileup['target_sequence'])
        start = big_seq.find(pileup['target_sequence'])
        indexs = start, start+length
        gene_df = combined_pileup.loc[indexs[0]:indexs[1]]
        gene_df.loc[:,'Sequence'] = pileup['sample_uuid']
        gene_df = gene_df.reset_index(drop=True)

        name = pileup['sample_uuid'] + '.pileup'
        gene_df.to_csv(name, sep='\t',header=False)
        payload = {'name': name}
        new_file = Files(name, open(name, 'rb'))
        db.session.add(new_file)
        db.session.commit()
        print(new_file.toJSON())
        os.remove(name)

    try:
        shutil.rmtree(tmp_location)
    except OSError:
        print('Failed to delete tmp')
    else:
        print('Deleted tmp')


def sequence(seqrun_file, api='https://api.freegenes.org',read_directory='./reads/'):
    # Add directory
    t0 = time.time()
    try:
        os.mkdir(read_directory)
    except OSError:
        print('Failed to create {}'.format(read_directory))
    else:
        print('Created {}'.format(read_directory))

    def download_file(url):
        local_filename = './reads/' + url.split('/')[-1]
        # NOTE the stream=True parameter below
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        # f.flush()
        return local_filename

    for k,v in seqrun_full['indexes'].items():
        reads = [download_file('{}/files/download/{}'.format(api,fastq['file_uuid'])) for fastq in v['fastqs']]
        sequence_link(k, pileups, reads)

    # Init by removing
    try:
        shutil.rmtree(read_directory)
    except OSError:
        print('Failed to delete {}'.format(read_directory))
    else:
        print('Deleted {}'.format(read_directory))

    t1 = time.time()
    total = t1-t0
    return {'Status': 'Complete',
            'Time': total}
    

