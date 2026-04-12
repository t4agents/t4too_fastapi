import { getUserDisplayName, supabase } from '../lib/supabase';

type NewUserProfile = {
    displayName?: string | null;
    photoURL?: string | null;
};

const DEFAULTS = {
    email: 'invoaice@gmail.com',
    name: 'Invoaice Agents',
    firstName: 'Invoaice',
    lastName: 'Agents',
    phone: '332-203-4114',
    position: 'CPA',
    facebook: 'https://facebook.com/invoaice',
    twitter: 'https://twitter.com/invoaice',
    github: 'https://github.com/invoaice',
    reddit: 'https://reddit.com/u/invoaice',
    country: 'Canada',
    state: 'Ontario',
    pin: '3322034114',
    zip: 'M5V 2T6',
    taxNo: 'invoaice123',
} as const;

const toNameParts = (fullName: string | null | undefined) => {
    const safeName = fullName?.trim() || DEFAULTS.name;
    const [first, ...rest] = safeName.split(' ').filter(Boolean);
    return {
        fullName: safeName,
        firstName: first || DEFAULTS.firstName,
        lastName: rest.join(' ') || DEFAULTS.lastName,
    };
};

export async function runNewUserProvisioning(profile?: NewUserProfile): Promise<void> {
    if (profile?.displayName || profile?.photoURL) {
        const { error } = await supabase.auth.updateUser({
            data: {
                full_name: profile?.displayName ?? undefined,
                avatar_url: profile?.photoURL ?? undefined,
            },
        });
        if (error) {
            throw error;
        }
    }

    const { data: userData, error: userError } = await supabase.auth.getUser();
    if (userError) {
        throw userError;
    }
    const user = userData.user;
    if (!user) {
        throw new Error('No authenticated user available for provisioning.');
    }

    const email = user.email ?? DEFAULTS.email;
    const displayName = profile?.displayName?.trim() || getUserDisplayName(user) || DEFAULTS.name;
    const avatar = profile?.photoURL?.trim() || (user.user_metadata?.avatar_url as string | undefined);
    const { firstName, lastName, fullName } = toNameParts(displayName);

    const baseIds = {
        id: user.id,
        ten_id: user.id,
        biz_id: user.id,
        owner_id: user.id,
    };

    const zmePayload = {
        ...baseIds,
        email,
        display_name: displayName,
        name: displayName,
        full_name: fullName,
        first_name: firstName,
        last_name: lastName,
        avatar: avatar ?? null,
        phone: DEFAULTS.phone,
        position: DEFAULTS.position,
        facebook: DEFAULTS.facebook,
        twitter: DEFAULTS.twitter,
        github: DEFAULTS.github,
        reddit: DEFAULTS.reddit,
        country: DEFAULTS.country,
        state: DEFAULTS.state,
        pin: DEFAULTS.pin,
        zip: DEFAULTS.zip,
        tax_no: DEFAULTS.taxNo,
    };

    const zbePayload = {
        ...baseIds,
        be_name: 'My Business',
        be_type: 'ME',
        be_email: email,
        be_phone: DEFAULTS.phone,
        be_contact: displayName,
    };

    const [zmeResult, zbeResult] = await Promise.all([
        supabase.from('zme').upsert(zmePayload, { onConflict: 'id', ignoreDuplicates: true }),
        supabase.from('zbe').upsert(zbePayload, { onConflict: 'id', ignoreDuplicates: true }),
    ]);

    if (zmeResult.error) {
        throw zmeResult.error;
    }
    if (zbeResult.error) {
        throw zbeResult.error;
    }
}
