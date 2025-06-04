import streamlit as st
import openai
import json
import tempfile
import os
from music21 import converter, key, meter, chord, roman, interval

# ✅ Initialize OpenAI client
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

st.title("🎼 Expressive Music Theory Assistant")
st.write("Upload a MIDI file to generate harmonic analysis and expressive teaching tips.")

# Upload MIDI file
uploaded_file = st.file_uploader("Upload MIDI file", type=["mid", "midi"])

# Analyze MIDI
if uploaded_file is not None:
    st.success("MIDI uploaded successfully! Analyzing...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Parse score with forced MIDI format
    score = converter.parse(tmp_path, format="midi")
    k = score.analyze('key')
    ts = score.recurse().getElementsByClass(meter.TimeSignature)[0]

    chords, rhythm_data, pitch_range_data, contour_data = [], [], [], []
    melody = score.parts[0].flatten().notes
    measures = score.parts[0].getElementsByClass('Measure')

    for m in measures:
        notes = m.notes
        try:
            if len(notes) >= 2:
                ch = chord.Chord(notes)
                rm = roman.romanNumeralFromChord(ch, k)
                chords.append(f"m.{m.measureNumber}: {rm.figure}")
            else:
                chords.append(f"m.{m.measureNumber}: not enough notes")
            rhythms = [n.quarterLength for n in notes]
            avg_rhythm = sum(rhythms) / len(rhythms) if rhythms else 0
            rhythm_data.append(f"m.{m.measureNumber}: avg rhythm = {avg_rhythm:.2f}")
            pitches = [n.pitch.midi for n in notes if n.isNote]
            if pitches:
                pr = max(pitches) - min(pitches)
                pitch_range_data.append(f"m.{m.measureNumber}: pitch range = {pr}")
            else:
                pitch_range_data.append(f"m.{m.measureNumber}: no pitch data")
        except:
            continue

    for i in range(1, len(melody)):
        try:
            if melody[i-1].isNote and melody[i].isNote:
                intvl = interval.Interval(melody[i-1], melody[i])
                contour_data.append(f"From m.{melody[i-1].measureNumber} to m.{melody[i].measureNumber}: {intvl.directedName}")
        except:
            continue

    output = {
        "key": str(k),
        "time_signature": ts.ratioString,
        "chords": chords,
        "rhythmic_complexity": rhythm_data,
        "pitch_ranges": pitch_range_data,
        "melodic_contour": contour_data
    }

    st.json(output)

    # GPT button
    if st.button("🎤 Generate Expressive Teaching Tips"):
        filtered_chords = [c for c in chords if "not enough" not in c][:10]
        filtered_rhythm = rhythm_data[:5]
        filtered_range = [r for r in pitch_range_data if "no pitch" not in r][:5]
        filtered_contour = contour_data[:5]

        prompt = f"""
        You are a music theory teacher for adult learners. You want to talk about expressivity, structure, and musical gesture.

        Key: {output["key"]}
        Time Signature: {output["time_signature"]}

        Chords:
        {chr(10).join(filtered_chords)}

        Rhythmic Highlights:
        {chr(10).join(filtered_rhythm)}

        Pitch Range Insights:
        {chr(10).join(filtered_range)}

        Melodic Contour:
        {chr(10).join(filtered_contour)}
        """

        messages = [
            {"role": "system", "content": "You are a friendly and expressive music theory teacher."},
            {"role": "user", "content": prompt}
        ]

        # ✅ Call OpenAI with the new SDK structure
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
    )
    gpt_text = response.choices[0].message.content.strip()
    st.markdown("### 🎓 GPT Teaching Tips")
    st.text_area("GPT Output", value=gpt_text, height=300)

    with open("gpt_expressive_analysis.txt", "w") as f:
        f.write(gpt_text)
    st.success("Saved as gpt_expressive_analysis.txt")

except Exception as e:
    st.error(f"OpenAI API call failed: {e}")

        gpt_text = response.choices[0].message.content.strip()
        st.markdown("### 🎓 GPT Teaching Tips")
        st.text_area("GPT Output", value=gpt_text, height=300)

        # Save result
        with open("gpt_expressive_analysis.txt", "w") as f:
            f.write(gpt_text)
        st.success("Saved as gpt_expressive_analysis.txt")

    # Save JSON
    if st.button("💾 Save JSON"):
        with open("analysis_output.json", "w") as f:
            json.dump(output, f, indent=2)
        st.success("Saved as analysis_output.json")
