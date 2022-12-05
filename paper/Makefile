.PHONY: clean compile

# Generate the pdf version of the paper
compile:
	docker run --rm \
	--volume ${PWD}:/data:z \
	--user $(id -u):$(id -g) \
	--env JOURNAL=joss openjournals/inara

# Clean outputs
clean:
	rm paper.pdf paper.jats -f
	rm media/ -rf