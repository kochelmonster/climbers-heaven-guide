export get_lang_field = (obj, prefix) ->
    try
        lang = document.documentElement.lang or "en"
    catch error
        lang = "en"
    name = prefix + "-" + lang
    return obj[name] or obj[prefix + "-en"]
