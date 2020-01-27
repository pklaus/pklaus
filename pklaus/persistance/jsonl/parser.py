import itertools
import json
#import rapidjson as json
from multiprocessing import Pool

class JsonlParser():
    """
    Helper to parse JSON Lines files (http://jsonlines.org/).

    Create an instance with the JSON Lines content as string.

    The class will help parsing the content efficiently
    (with multiple workers).

    (Before using this class, read the whole file into memory.
    Most jsonl files should fit.)
    """
    def __init__(self, data, nworkers=8):
        self.data  = data
        self.nworkers = nworkers
        data_len = len(data)
        self.split_at = '\n'
        # determine the data boundaries for each worker
        chunks = []
        # Look for line
        nl_pos = 0
        offset = 0
        for i in range(nworkers-1):
            look_at = (data_len // nworkers) * (i+1)
            nl_pos = data.find(self.split_at, look_at)
            #print(f"look_at:0x{look_at:08X} -> nl_pos:0x{nl_pos:08X}")
            if nl_pos != -1:
                chunk = data[offset:nl_pos+1]
            else:
                nl_pos = len(data) - 1
                chunk = data[offset:]
            offset = nl_pos + 1
            chunks.append(chunk)
            if nl_pos == -1:
                break
        if nl_pos != len(data):
            chunk = data[offset:]
            chunks.append(chunk)
        #for i, chunk in enumerate(chunks):
        #    print(f"Chunk {i} length:0x{len(chunk):08X} ({len(chunk)/1024/1024:.3f}MiB)")
        self.chunks = chunks

    @staticmethod
    def parse_chunk(chunk):
        lines = chunk.strip().split('\n')
        messages = []
        for line in lines:
            messages.append(json.loads(line))
            try:
                messages.append(json.loads(line))
            except ValueError as e:
                print(repr(line))
        return messages

    def parse(self):
        if self.nworkers <= 1:
            return JsonlParser.parse_chunk(self.chunks[0])
        else:
            with Pool(self.nworkers) as p:
                return list(itertools.chain(*p.map(JsonlParser.parse_chunk, self.chunks)))

def main():
    import argparse, time
    parser = argparse.ArgumentParser()
    parser.add_argument('jsonlfile')
    parser.add_argument('--nworkers', '-n', type=int, default=8)
    args = parser.parse_args()
    with open(args.jsonlfile, 'r') as f:
        content = f.read()
    start = time.time()
    jp = JsonlParser(content, nworkers=args.nworkers)
    data = jp.parse()
    end = time.time()
    print(f"{len(data)} JSON Lines read from {args.jsonlfile} in {(end-start)*1000:.2f} ms.")

if __name__ == "__main__": main()
