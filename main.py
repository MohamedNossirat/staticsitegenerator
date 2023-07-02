import os
import frontmatter
from slugify import slugify
from markdown2 import markdown
from jinja2 import Environment, FileSystemLoader
import htmlmin
from bs4 import BeautifulSoup
import shutil
from json import load

env = Environment(loader=FileSystemLoader(searchpath="./templates"))


# The generator Class
class StaticSiteGenerator:
    def generateAssets(self):
        os.makedirs("dist/assets", exist_ok=True)
        assets_files = [
            file
            for file in os.listdir("assets")
            if os.path.isfile(os.path.join(f"assets/{file}"))
            and not file.startswith(".")
        ]
        assets_dirs = [
            dir
            for dir in os.listdir("assets")
            if os.path.isdir(os.path.join(f"assets/{dir}"))
        ]
        # Generate all assets in dist folder
        for file in assets_files:
            with open(f"assets/{file}", "rb") as asset_file:
                with open(f"dist/assets/{file}", "wb") as dist_file:
                    dist_file.write(asset_file.read())

        for dir in assets_dirs:
            os.makedirs(f"dist/assets/{dir}", exist_ok=True)
            files = [
                file
                for file in os.listdir(f"assets/{dir}")
                if os.path.isfile(os.path.join(f"assets/{dir}/{file}"))
            ]
            for file in files:
                with open(f"assets/{dir}/{file}", "rb") as subasset_file:
                    with open(f"dist/assets/{dir}/{file}", "wb") as subassetsdst_file:
                        subassetsdst_file.write(subasset_file.read())

    def generateIndex(self):
        with open('user.conf.json') as config_file:
            userconf = load(config_file)
        index_template = env.get_template("index.html")
        with open("dist/index.html", "w") as index_file:
            index_file.write(index_template.render(config=userconf['config']))

    def _load_pages(self):
        pages = [
            page
            for page in os.listdir("content/pages")
            if os.path.isfile(os.path.join(f"content/pages/{page}"))
        ]
        pages_data = []
        for page in pages:
            with open(f"content/pages/{page}") as md_page:
                md = frontmatter.load(md_page)
                md.metadata["slug"] = slugify(md.metadata["title"])
                pages_data.append(
                    {
                        "metadata": md.metadata,
                        "content": htmlmin.minify(
                            self._set_sections_tags(
                                markdown(
                                    md.content,
                                    extras=["fenced-code-blocks", "code-friendly"],
                                )
                            )[0]
                        ),
                        "toc": self._set_sections_tags(markdown(md.content))[1],
                    }
                )
        return pages_data

    def _set_sections_tags(self, md_content):
        soup = BeautifulSoup(md_content, "html.parser")
        toc = {tag.text: f"#{slugify(tag.text)}" for tag in soup.find_all("h2")}
        for h2 in soup.find_all("h2"):
            h2.attrs["id"] = slugify(h2.text)
        return str(soup.prettify()), toc

    def generatePages(self):
        pages_data = self._load_pages()
        os.makedirs("dist/pages", exist_ok=True)
        for page in pages_data:
            page_tempate = env.get_template("post.html")
            with open(f"dist/pages/{page['metadata']['slug']}.html", "w") as post_html:
                post_html.write(page_tempate.render(post=page))
    def generateTags(self):
        # Momo
        pages_data=self._load_pages()
        tags = set()
        for page in pages_data:
            tags.update(page['metadata']['tags'])
        os.makedirs('dist/tags',exist_ok=True)
        for tag in tags:
            tag_template=env.get_template('tag.html')
            with open(f'dist/tags/{slugify(tag)}.html', 'w') as tag_html:
                tag_html.write(tag_template.render(
                    tag=tag,
                    pages=pages_data
                ))
    def generateBlogPage(self):
        pages = self._load_pages()
        blog_template = env.get_template("blog.html")
        with open("dist/blog.html", "w") as blog_html:
            blog_html.write(blog_template.render(pages=pages))

    def generate(self):
        shutil.rmtree('dist', ignore_errors=True)
        self.generateAssets()
        self.generateIndex()
        self.generatePages()
        self.generateBlogPage()
        self.generateTags()


if __name__ == "__main__":
    StaticSiteGenerator().generate()
