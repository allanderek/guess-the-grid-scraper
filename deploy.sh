# To upload this to github pages do:
# TODO: Can I check that everything is committed on master first?
# TODO: Turn this into a Python script.
git checkout gh-pages &&
git merge master &&
python main.py &&
# TODO: check if index.html has actually changed.
git add index.html &&
git commit -m "Latest build and commit to gh-pages" &&
git push origin gh-pages