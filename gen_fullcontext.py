from pathlib import Path

import pyopenjtalk
from nnmnkwii.io import hts
from tqdm.auto import tqdm
from ttslearn.logger import getLogger
from ttslearn.util import lab2phonemes

logger = getLogger(verbose=1)

ita_corpus_dir = Path("/home/ryuichi/data/ita-corpus")
ita_db_root = Path("/home/ryuichi/data/ita")

out_dir = Path("/home/ryuichi/data/ita-lab")


def get_valid_utts(spk, emotion):
    N = 0
    cnt = 0
    utt_ids, texts = [], []
    recitation = emotion is None
    if recitation:
        transcript = ita_corpus_dir / "recitation_transcript_utf8.txt"
    else:
        transcript = ita_corpus_dir / "emotion_transcript_utf8.txt"

    with open(ita_corpus_dir / transcript) as f:
        for line in tqdm(f):
            s = line.split(":")
            utt_id = s[0].strip()
            if recitation:
                utt_id = utt_id.lower().replace("324_", "")
            else:
                utt_id = utt_id.lower().replace("emotion100_", f"emo{emotion}")
            text, mora = s[1].split(",")
            text, mora = text.strip(), mora.strip()

            ph_from_mora = pyopenjtalk.g2p(mora).lower()
            ph_from_text = pyopenjtalk.g2p(text).lower()
            N += 1

            if recitation:
                lab_path = ita_db_root / f"{spk}/recitation/" / (utt_id + ".lab")
            else:
                lab_path = (
                    ita_db_root
                    / f"{spk}/emotion/{emotion.lower()}/"
                    / (utt_id + ".lab")
                )
            labels = hts.load(lab_path)
            assert "sil" in labels.contexts[0] and "sil" in labels.contexts[-1]
            ph_in_lab = " ".join(lab2phonemes(labels)[1:-1]).lower()

            # no G2P errors
            if ph_from_text == ph_from_mora and len(ph_from_text) == len(ph_in_lab):
                ok = True
                openjtalk_input = text
            # G2p errors, but phones are correct
            elif len(ph_from_mora) == len(ph_in_lab):
                ok = True
                openjtalk_input = mora
                logger.warning(f"{utt_id}: found G2P errors")
                logger.debug(f"Labels: {ph_in_lab}")
                logger.debug(f"Open JTalk results: {ph_from_text}")
            else:
                ok = False
                openjtalk_input = None

            if ok:
                full_context_labels = hts.HTSLabelFile.create_from_contexts(
                    pyopenjtalk.extract_fullcontext(openjtalk_input)
                )

                ph1 = " ".join(lab2phonemes(labels)).lower()
                ph2 = " ".join(lab2phonemes(full_context_labels)).lower()
                assert len(ph1) == len(ph2)
                for k, v in [("b ", "v "), ("e i", "e e"), ("ty u", "ch u")]:
                    ph1 = ph1.replace(k, v)
                    ph2 = ph2.replace(k, v)
                if ph1 != ph2:
                    logger.warning(f"{utt_id}: found phoneme mismatch")
                    logger.debug(f"Labels: {ph1}")
                    logger.debug(f"Open JTalk results: {ph2}")
                    continue
                assert ph1 == ph2
                assert "sil" in full_context_labels.contexts[0] and "sil" in full_context_labels.contexts[-1]
                utt_ids.append(utt_id)
                texts.append(openjtalk_input)
            else:
                cnt += 1

    logger.info(f"Total utts: {N}, excluded: {cnt}, generated number of labels: {N - cnt}")
    return utt_ids, texts


def write_fullcontext(utt_ids, texts, spk, emotion, out_dir):
    recitation = emotion is None
    if recitation:
        lab_dir = out_dir / spk / "recitation"
    else:
        lab_dir = out_dir / spk / "emotion" / emotion.lower()
    lab_dir.mkdir(exist_ok=True, parents=True)

    for utt_id, text in zip(utt_ids, texts):
        if recitation:
            lab_path = ita_db_root / spk / "recitation" / (utt_id + ".lab")
        else:
            lab_path = (
                ita_db_root / spk / "emotion" / emotion.lower() / (utt_id + ".lab")
            )
        labels = hts.load(lab_path)

        full_context_labels = hts.HTSLabelFile.create_from_contexts(
            pyopenjtalk.extract_fullcontext(text)
        )
        full_context_labels.start_times = labels.start_times
        full_context_labels.end_times = labels.end_times

        with open(lab_dir / (f"{spk}_{utt_id}.lab"), "w") as of:
            of.write(str(full_context_labels))


out_dir.mkdir(exist_ok=True, parents=True)


for spk in ["itako", "zundamon", "methane"]:
    # Recitation
    logger.info(f"spk: {spk}, recitation")
    utt_ids, texts = get_valid_utts(spk, None)
    write_fullcontext(utt_ids, texts, spk, None, out_dir)

    # Emotion
    for emotion in ["Normal", "Sexy", "Tsun", "Ama"]:
        logger.info(f"spk: {spk}, emotion: {emotion}")
        utt_ids, texts = get_valid_utts(spk, emotion)
        write_fullcontext(utt_ids, texts, spk, emotion, out_dir)
