show-releases:
    echo "previous releases:" && git tag | tail -n3

release VERSION:
   @if [ $(git rev-parse --abbrev-ref HEAD) = "master" ]; then \
        git pull origin master; \
        git tag {{ VERSION }} && git push origin {{ VERSION }} && gh release create {{ VERSION }} --notes ""; \
    else \
        echo "Not on master branch"; \
        exit 1; \
    fi
