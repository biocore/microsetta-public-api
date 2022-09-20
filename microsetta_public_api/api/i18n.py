from flask_babel import gettext


def declare_enum_values():
    # The public api can at times expect parameters that need to be
    # translated into the appropriate language before processing can
    # continue. We define those values here so that babel picks them
    # up for translation.

    # Ensure that EN_US_KEY is added to the POT file
    gettext('en_US')

    gettext('Adult')
    gettext('Asia')
    gettext('Child')
    gettext('Elderly')
    gettext('Europe')
    gettext('India-Bangladesh')
    gettext('Infant')
    gettext('Mouth')
    gettext('North America')
    gettext('Oceania')
    gettext('Office Surface')
    gettext('Oral')
    gettext('Other')
    gettext('Skin')
    gettext('South America')
    gettext('Southeast Africa')
    gettext('Stool')
    gettext('Teen')
    gettext('You')
