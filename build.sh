# bin/bash

echo "fetch data from all three lk-, fa- and dw-data repos"
rm -r rdf
mkdir rdf

wget -O lk.zip https://github.com/semantic-kraus/lk-data/archive/refs/heads/gh-pages.zip
unzip lk
mkdir rdf/lk
mv lk-data-gh-pages/*.ttl rdf/lk
mv lk-data-gh-pages/*.trig rdf/lk
rm lk.zip
rm -rf lk-data-gh-pages

wget -O fa.zip https://github.com/semantic-kraus/fa-data/archive/refs/heads/gh-pages.zip
unzip fa.zip
mkdir rdf/fa
mv fa-data-gh-pages/*.ttl rdf/fa
mv fa-data-gh-pages/*.trig rdf/fa
rm fa.zip
rm -rf fa-data-gh-pages

wget -O dw.zip https://github.com/semantic-kraus/dw-data/archive/refs/heads/gh-pages.zip
unzip dw.zip
mkdir rdf/dw
mv dw-data-gh-pages/*.ttl rdf/dw
mv dw-data-gh-pages/*.trig rdf/dw
rm dw.zip
rm dw.zip -rf dw-data-gh-pages

echo "rdf turtle data fetched"

echo "combine all turtle files to one file"
pip install -r requirements.txt
python ./scripts/owl_inverse_props_and_combine.py
echo "finished creating inverse triples and combining all turtle files to one file"
echo "created file: ./rdf/sk_combined.trig"

echo "create index.html and copy named graph to html folder"
mkdir html
mv rdf/sk_combined.trig html/sk_combined.trig
python ./scripts/make_index.py