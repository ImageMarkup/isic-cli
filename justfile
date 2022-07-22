show-releases:
    echo "previous releases:" && git tag | tail -n3

release VERSION:
    git tag {{ VERSION }} && git push origin {{ VERSION }} && gh release create {{ VERSION }} --notes ""
