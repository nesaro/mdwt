import rdflib
import glob
import os
import subprocess
from io import StringIO


def main():
    g = rdflib.Graph()
    ttl_path_glob = os.path.join(os.environ['HOME'], 'wiki/*.ttl')
    md_path_glob = os.path.join(os.environ['HOME'], 'wiki/*.md')
    print(ttl_path_glob)
    for path in glob.glob(ttl_path_glob):
        print(path)
        result = g.parse(path, format="turtle")

    files_with_ttl = subprocess.run(["grep", "-l", "\[\[\[ttl"] +  glob.glob(md_path_glob),
                                    capture_output=True).stdout.decode()

    for path in files_with_ttl.split("\n"):
        if not path:
            continue
        with open(path) as f:
            file_content = f.read()
            start_seen = False
            content=[]
            for line in file_content.split("\n"):
                if line.startswith("[[[ttl"):
                    start_seen = True
                    continue
                elif start_seen and line.startswith("]]]"):
                    break
                elif not start_seen:
                    continue
                content.append(line)
            else:
                print("BROKEN")
                continue
            string_io = StringIO("\n".join(content))
            g.parse(string_io, format="turtle")


                

    qres = g.query(
        """SELECT DISTINCT ?a
           WHERE {
              ?a rdf:type "person"
           }""")

    print([str(x[0]) for x in qres])


if __name__ == "__main__":
    main()
