JVSDIR=~/data/ita
OUTDIR=~/data/ita_r9y9

mkdir -p $OUTDIR

# link all wave file
for speaker in itako zundamon methane; do
    echo $speaker
    for corpus in recitation; do
        mkdir -p $OUTDIR/$speaker/$corpus
        find $JVSDIR/$speaker/$corpus -name '*.wav' | parallel ln {} $OUTDIR/$speaker/$corpus/${speaker}_{/}
	find $JVSDIR/$speaker/$corpus -name '*.lab' | parallel ln {} $OUTDIR/$speaker/$corpus/${speaker}_{/}
    done
    for corpus in ama normal sexy tsun; do
        mkdir -p $OUTDIR/$speaker/emotion/$corpus
        find $JVSDIR/$speaker/emotion/$corpus -name '*.wav' | parallel ln {} $OUTDIR/$speaker/emotion/$corpus/${speaker}_{/}
	find $JVSDIR/$speaker/emotion/$corpus -name '*.lab' | parallel ln {} $OUTDIR/$speaker/emotion/$corpus/${speaker}_{/}
    done
done
